"""Wi-Fi networks through NetworkManager's nmcli (Guided 1.4: the Wi-Fi window, like the Bluetooth one).

Only SSIDs, signal, security and the known/connected state leave this module. Passwords go straight to nmcli and are
never logged or returned.
"""

import os
import subprocess

from guided.bluetooth import subprocess_env

TIMEOUT_S = 8
CONNECT_TIMEOUT_S = 45


def _nmcli(args, timeout, run=subprocess.run, environ=None):
    return run(["nmcli", *args], capture_output=True, text=True, timeout=timeout, env=subprocess_env(os.environ if environ is None else environ))


def split_terse(line):
    """One `nmcli -t` line -> fields (':' separates, '\\:' and '\\\\' are escaped inside a field). Pure."""
    fields, cur, esc = [], [], False
    for ch in line:
        if esc:
            cur.append(ch)
            esc = False
        elif ch == "\\":
            esc = True
        elif ch == ":":
            fields.append("".join(cur))
            cur = []
        else:
            cur.append(ch)
    fields.append("".join(cur))
    return fields


def parse_networks(text, known):
    """`nmcli -t -f IN-USE,SSID,SIGNAL,SECURITY dev wifi list` -> one entry per SSID (strongest access point), the
    connected one first, then known networks, then the rest by signal. Hidden networks (no SSID) are left out. Pure."""
    best = {}
    for line in text.splitlines():
        parts = split_terse(line)
        if len(parts) < 4:
            continue
        in_use, ssid, signal, security = parts[0].strip(), parts[1], parts[2], parts[3].strip()
        if not ssid:
            continue
        try:
            level = max(0, min(100, int(signal)))
        except ValueError:
            level = 0
        entry = best.get(ssid)
        if entry is None:
            entry = best[ssid] = {"ssid": ssid, "signal": level, "secure": bool(security) and security != "--", "connected": False, "known": ssid in known}
        entry["signal"] = max(entry["signal"], level)
        entry["connected"] = entry["connected"] or in_use == "*"
    return sorted(best.values(), key=lambda n: (not n["connected"], not n["known"], -n["signal"], n["ssid"].lower()))


def known_networks(run=subprocess.run, environ=None):
    """{ssid: connection name} of the saved Wi-Fi connections."""
    out = {}
    listing = _nmcli(["-t", "-f", "NAME,TYPE", "connection", "show"], TIMEOUT_S, run, environ)
    for line in listing.stdout.splitlines():
        parts = split_terse(line)
        if len(parts) >= 2 and parts[1] == "802-11-wireless":
            name = parts[0]
            ssid = _nmcli(["-t", "-g", "802-11-wireless.ssid", "connection", "show", "id", name], TIMEOUT_S, run, environ).stdout.strip()
            out[ssid or name] = name
    return out


def wifi_state(run=subprocess.run, environ=None):
    """'on', 'off' or 'missing' (no nmcli / no Wi-Fi device)."""
    try:
        radio = _nmcli(["radio", "wifi"], TIMEOUT_S, run, environ)
        if radio.returncode != 0:
            return "missing"
        devices = _nmcli(["-t", "-f", "TYPE", "device"], TIMEOUT_S, run, environ).stdout.split()
        if "wifi" not in devices:
            return "missing"
        return "on" if radio.stdout.strip() == "enabled" else "off"
    except Exception:
        return "missing"


def list_networks(rescan=False, run=subprocess.run, environ=None, log=None):
    """{"state": on|off|missing, "networks": [...]}; scans first when asked (nmcli waits for the scan)."""
    try:
        state = wifi_state(run, environ)
        if state != "on":
            return {"state": state, "networks": []}
        known = known_networks(run, environ)
        listing = _nmcli(["-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes" if rescan else "no"], 30 if rescan else TIMEOUT_S, run, environ)
        if listing.returncode != 0 and log:
            log(f"nmcli wifi list exited with {listing.returncode}")
        return {"state": state, "networks": parse_networks(listing.stdout, known)}
    except Exception as error:
        if log:
            log(f"listing networks failed: {type(error).__name__}")
        return {"state": "missing", "networks": []}


def _reason(result):
    """A short machine reason from nmcli's error (no SSIDs or secrets in it)."""
    text = f"{result.stdout}\n{result.stderr}".lower()
    if "secrets were required" in text or "no secrets" in text or "password" in text or "802-1x" in text or "psk" in text:
        return "password"
    if "no network with ssid" in text:
        return "gone"
    return "failed"


def connect(ssid, password=None, run=subprocess.run, environ=None, log=None):
    """{"ok": bool, "reason": ''|password|gone|failed}. A saved network comes up by its connection; a new one is joined
    with the password (or without one when it is open)."""
    ssid = str(ssid or "")
    if not ssid or len(ssid) > 64:
        return {"ok": False, "reason": "failed"}
    try:
        name = known_networks(run, environ).get(ssid)
        if name and not password:
            result = _nmcli(["connection", "up", "id", name], CONNECT_TIMEOUT_S, run, environ)
        else:
            args = ["device", "wifi", "connect", ssid]
            if password:
                args += ["password", str(password)]
            result = _nmcli(args, CONNECT_TIMEOUT_S, run, environ)
        if result.returncode == 0:
            return {"ok": True, "reason": ""}
        reason = _reason(result)
        if log:
            log(f"connect failed ({reason}, exit {result.returncode})")
        return {"ok": False, "reason": reason}
    except subprocess.TimeoutExpired:
        return {"ok": False, "reason": "failed"}
    except Exception as error:
        if log:
            log(f"connect failed: {type(error).__name__}")
        return {"ok": False, "reason": "failed"}


def disconnect(ssid, run=subprocess.run, environ=None, log=None):
    """Takes the saved connection of this network down (the profile stays saved)."""
    try:
        name = known_networks(run, environ).get(str(ssid or ""))
        if not name:
            return False
        return _nmcli(["connection", "down", "id", name], TIMEOUT_S, run, environ).returncode == 0
    except Exception as error:
        if log:
            log(f"disconnect failed: {type(error).__name__}")
        return False

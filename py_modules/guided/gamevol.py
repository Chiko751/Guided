"""Volume of the running game only (Linux, PipeWire / PulseAudio): the game's processes carry SteamAppId / SteamGameId
in their environment (Proton, native, non-Steam shortcuts alike); their audio streams (sink inputs) are found by
application.process.id and changed with pactl. Nothing else is touched."""
import json
import os
import subprocess
import time

_cache: dict = {}


def _env() -> dict:
    env = dict(os.environ)
    uid = os.getuid() if hasattr(os, "getuid") else 0
    env.setdefault("XDG_RUNTIME_DIR", f"/run/user/{uid}")
    return env


def _pids(app_id: str) -> set:
    """PIDs whose environment names this game; cached for 3 s (reading every /proc/*/environ costs a few ms)."""
    hit = _cache.get(app_id)
    if hit and time.monotonic() - hit[0] < 3:
        return hit[1]
    want = {f"SteamAppId={app_id}".encode(), f"SteamGameId={app_id}".encode()}
    out = set()
    for name in os.listdir("/proc"):
        if not name.isdigit():
            continue
        try:
            with open(f"/proc/{name}/environ", "rb") as f:
                env = f.read()
        except OSError:
            continue
        if any(w in env.split(b"\0") for w in want):
            out.add(int(name))
    _cache[app_id] = (time.monotonic(), out)
    return out


# helper processes of Steam, Proton / Wine and the runtime: never the name of the game's own audio stream
_HELPERS = {"steam", "steam-runtime-l", "reaper", "srt-bwrap", "pv-adverb", "python3", "wineserver", "services", "winedevice",
            "svchost", "plugplay", "explorer", "rpcss", "tabtip", "xalia", "lsass", "conhost", "start", "winedbg", "dualsense_wired"}


def _names(pids: set) -> set:
    """Process names of the game (without .exe), for audio streams that carry no process id (Proton: seen with a
    non-Steam game - the stream only names itself, e.g. "PRAGMATA" for PRAGMATA.exe)."""
    out = set()
    for pid in pids:
        try:
            with open(f"/proc/{pid}/comm") as f:
                n = f.read().strip().lower()
        except OSError:
            continue
        n = n[:-4] if n.endswith(".exe") else n
        if len(n) >= 3 and n not in _HELPERS:
            out.add(n)
    return out


def _streams(app_id: str) -> list:
    r = subprocess.run(["pactl", "-f", "json", "list", "sink-inputs"], capture_output=True, text=True, timeout=4, env=_env())
    if r.returncode != 0:
        return []
    pids = _pids(app_id)
    names = None
    found = []
    for s in json.loads(r.stdout or "[]"):
        props = s.get("properties", {})
        try:
            pid = int(props.get("application.process.id") or 0)
        except ValueError:
            pid = 0
        if pid:
            if pid in pids:
                found.append(s)
            continue
        # no process id: match the stream's name against the game's process names
        if names is None:
            names = _names(pids)
        label = str(props.get("application.name") or props.get("node.name") or "").strip().lower()
        label = label[:-4] if label.endswith(".exe") else label
        if label and label in names:
            found.append(s)
    return found


def get(app_id: str) -> dict:
    if not str(app_id).isdigit():
        return {"ok": False, "error": "bad-id"}
    streams = _streams(str(app_id))
    if not streams:
        return {"ok": True, "streams": 0}
    vols = [int(str(c.get("value_percent", "100%")).rstrip("%") or 100) for s in streams for c in (s.get("volume") or {}).values()]
    return {"ok": True, "streams": len(streams), "volume": round(sum(vols) / len(vols)) if vols else 100,
            "muted": all(s.get("mute") for s in streams)}


def set_volume(app_id: str, value: int) -> dict:
    if not str(app_id).isdigit():
        return {"ok": False, "error": "bad-id"}
    value = max(0, min(150, int(value)))
    streams = _streams(str(app_id))
    for s in streams:
        subprocess.run(["pactl", "set-sink-input-volume", str(s["index"]), f"{value}%"], capture_output=True, timeout=4, env=_env())
    return {"ok": bool(streams), "streams": len(streams), "volume": value}

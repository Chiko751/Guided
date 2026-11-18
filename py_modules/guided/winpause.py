"""Pause / resume games on Windows (Guided Windows, like the Decky plugin "PauseGames" does on Linux with SIGSTOP/SIGCONT).

A game's processes are found through its install folder: Steam's library folders (libraryfolders.vdf) -> the app's
appmanifest_<appid>.acf -> installdir; every running process whose executable lives in that folder (or, when Windows does
not tell the path - anti-cheat protected games - whose file name matches an .exe in that folder) belongs to the game,
plus their child processes. Pausing suspends every thread of those processes (NtSuspendProcess); resuming undoes it.
Protected processes refuse to be suspended: they are reported as "failed" and left running.

The paused state is kept here (appid -> pids) so a resume always matches the pause, and everything is resumed when the
plugin unloads (a frozen game must never be left behind).
"""
import ctypes
import json
import os
import re
import sys
import threading

_WIN = sys.platform == "win32"
_lock = threading.Lock()
_paused = {}  # appid -> [pid, ...] suspended by us
_exe_cache = {}  # appid -> (install dir, {exe names})
_state_file = None  # JSON with the suspended pids, so a crashed backend can resume them on its next start


def set_state_file(path):
    global _state_file
    _state_file = path


def _save():
    if not _state_file:
        return
    try:
        with open(_state_file, "w", encoding="utf-8") as fh:
            json.dump({str(k): v for k, v in _paused.items()}, fh)
    except OSError:
        pass


def recover():
    """Resume whatever a previous (crashed or killed) backend left suspended."""
    if not (_WIN and _state_file):
        return 0
    try:
        with open(_state_file, encoding="utf-8") as fh:
            left = json.load(fh)
    except (OSError, ValueError):
        return 0
    n = 0
    for pids in left.values():
        for pid in pids:
            # resuming a process that is not suspended (or a reused pid) does nothing
            n += 1 if _nt(_ntdll.NtResumeProcess, int(pid)) else 0
    _paused.clear()
    _save()
    return n

if _WIN:
    from ctypes import wintypes

    _k32 = ctypes.WinDLL("kernel32", use_last_error=True)
    _ntdll = ctypes.WinDLL("ntdll")
    _TH32CS_SNAPPROCESS = 0x2
    _PROCESS_SUSPEND_RESUME = 0x0800
    _PROCESS_QUERY_LIMITED_INFORMATION = 0x1000

    class _PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD), ("th32ProcessID", wintypes.DWORD),
                    ("th32DefaultHeapID", ctypes.c_void_p), ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long), ("dwFlags", wintypes.DWORD),
                    ("szExeFile", ctypes.c_wchar * 260)]

    _k32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    _k32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    _k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(_PROCESSENTRY32W)]
    _k32.OpenProcess.restype = wintypes.HANDLE
    _k32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    _k32.CloseHandle.argtypes = [wintypes.HANDLE]
    _k32.QueryFullProcessImageNameW.argtypes = [wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD)]
    _ntdll.NtSuspendProcess.argtypes = [wintypes.HANDLE]
    _ntdll.NtResumeProcess.argtypes = [wintypes.HANDLE]

    def _processes():
        """[(pid, parent pid, exe name lower)]"""
        snap = _k32.CreateToolhelp32Snapshot(_TH32CS_SNAPPROCESS, 0)
        if not snap or snap == wintypes.HANDLE(-1).value:
            return []
        out = []
        try:
            entry = _PROCESSENTRY32W()
            entry.dwSize = ctypes.sizeof(_PROCESSENTRY32W)
            ok = _k32.Process32FirstW(snap, ctypes.byref(entry))
            while ok:
                out.append((int(entry.th32ProcessID), int(entry.th32ParentProcessID), entry.szExeFile.lower()))
                ok = _k32.Process32NextW(snap, ctypes.byref(entry))
        finally:
            _k32.CloseHandle(snap)
        return out

    def _image_path(pid):
        h = _k32.OpenProcess(_PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
        if not h:
            return None
        try:
            buf = ctypes.create_unicode_buffer(1024)
            size = wintypes.DWORD(1024)
            return buf.value if _k32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)) else None
        finally:
            _k32.CloseHandle(h)

    _u32 = ctypes.WinDLL("user32", use_last_error=True)
    _WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
    _u32.EnumWindows.argtypes = [_WNDENUMPROC, wintypes.LPARAM]
    _u32.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _u32.GetWindowThreadProcessId.restype = wintypes.DWORD
    _u32.IsWindowVisible.argtypes = [wintypes.HWND]
    _u32.GetWindow.argtypes = [wintypes.HWND, ctypes.c_uint]
    _u32.GetWindow.restype = wintypes.HWND
    _u32.GetWindowTextLengthW.argtypes = [wintypes.HWND]
    _u32.GetForegroundWindow.restype = wintypes.HWND
    _u32.SetForegroundWindow.argtypes = [wintypes.HWND]
    _u32.ShowWindow.argtypes = [wintypes.HWND, ctypes.c_int]
    _u32.IsIconic.argtypes = [wintypes.HWND]
    _u32.BringWindowToTop.argtypes = [wintypes.HWND]
    _u32.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    _u32.keybd_event.argtypes = [ctypes.c_ubyte, ctypes.c_ubyte, wintypes.DWORD, ctypes.c_void_p]
    _k32.GetCurrentThreadId.restype = wintypes.DWORD

    def _pid_of(hwnd):
        pid = wintypes.DWORD()
        _u32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        return int(pid.value)

    def _main_windows(pids):
        """Visible, unowned top-level windows with a title that belong to these processes."""
        found = []

        def cb(hwnd, _):
            if _pid_of(hwnd) in pids and _u32.IsWindowVisible(hwnd) and not _u32.GetWindow(hwnd, 4) and _u32.GetWindowTextLengthW(hwnd) > 0:
                found.append(hwnd)
            return True
        _u32.EnumWindows(_WNDENUMPROC(cb), 0)
        return found

    def _nt(fn, pid):
        h = _k32.OpenProcess(_PROCESS_SUSPEND_RESUME, False, pid)
        if not h:
            return False
        try:
            return fn(h) == 0  # STATUS_SUCCESS
        finally:
            _k32.CloseHandle(h)


def _steam_path():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            return winreg.QueryValueEx(key, "SteamPath")[0]
    except Exception:
        return r"C:\Program Files (x86)\Steam"


def _libraries():
    steam = _steam_path()
    libs = [os.path.normpath(steam)]
    try:
        with open(os.path.join(steam, "steamapps", "libraryfolders.vdf"), encoding="utf-8", errors="replace") as fh:
            for m in re.finditer(r'"path"\s+"([^"]+)"', fh.read()):
                path = os.path.normpath(m.group(1).replace("\\\\", "\\"))
                if path not in libs:
                    libs.append(path)
    except OSError:
        pass
    return libs


def _install_dir(appid):
    for lib in _libraries():
        manifest = os.path.join(lib, "steamapps", f"appmanifest_{appid}.acf")
        try:
            with open(manifest, encoding="utf-8", errors="replace") as fh:
                m = re.search(r'"installdir"\s+"([^"]+)"', fh.read())
        except OSError:
            continue
        if m:
            path = os.path.join(lib, "steamapps", "common", m.group(1))
            if os.path.isdir(path):
                return os.path.normpath(path)
    return None


def _game_exes(appid):
    """(install dir, {exe file names, lower case}) - cached per app."""
    if appid in _exe_cache:
        return _exe_cache[appid]
    root = _install_dir(appid)
    names = set()
    if root:
        base = root.count(os.sep)
        for dirpath, dirnames, filenames in os.walk(root):
            if dirpath.count(os.sep) - base >= 5:
                dirnames[:] = []
            for f in filenames:
                if f.lower().endswith(".exe"):
                    names.add(f.lower())
    _exe_cache[appid] = (root, names)
    return _exe_cache[appid]


def _game_pids(appid):
    root, names = _game_exes(appid)
    if not root:
        return []
    prefix = root.lower().rstrip("\\") + "\\"
    procs = _processes()
    mine = set()
    for pid, _parent, name in procs:
        if name not in names:
            continue
        path = _image_path(pid)
        # path known: must be inside the game folder; unknown (protected process): the file name has to do
        if path is None or path.lower().startswith(prefix):
            mine.add(pid)
    # plus their children (crash handlers, helper processes started by the game)
    grew = True
    while grew:
        grew = False
        for pid, parent, _name in procs:
            if parent in mine and pid not in mine:
                mine.add(pid)
                grew = True
    return sorted(mine)


def pause(appid):
    """{"ok": bool, "paused": n, "failed": n, "reason": ...}"""
    if not _WIN:
        return {"ok": False, "paused": 0, "failed": 0, "reason": "unsupported"}
    appid = int(appid)
    with _lock:
        if appid in _paused:
            return {"ok": True, "paused": len(_paused[appid]), "failed": 0, "reason": "already"}
        pids = _game_pids(appid)
        if not pids:
            return {"ok": False, "paused": 0, "failed": 0, "reason": "notfound"}
        done, failed = [], 0
        for pid in pids:
            if _nt(_ntdll.NtSuspendProcess, pid):
                done.append(pid)
            else:
                failed += 1
        if done:
            _paused[appid] = done
            _save()
        return {"ok": bool(done), "paused": len(done), "failed": failed, "reason": "" if done else "protected"}


def resume(appid):
    if not _WIN:
        return {"ok": False, "resumed": 0}
    appid = int(appid)
    with _lock:
        pids = _paused.pop(appid, [])
        n = sum(1 for pid in pids if _nt(_ntdll.NtResumeProcess, pid))
        _save()
        return {"ok": True, "resumed": n}


def is_foreground(appid):
    """True when the foreground window belongs to the game; None when Windows does not tell."""
    if not _WIN:
        return None
    hwnd = _u32.GetForegroundWindow()
    if not hwnd:
        return None
    return _pid_of(hwnd) in set(_game_pids(int(appid)))


def raise_app(appid):
    """Bring the game's window to the front. A background process may not simply take the foreground; pressing and
    releasing Alt first (what Windows accepts as user input) and briefly attaching to the foreground thread lets it."""
    if not _WIN:
        return False
    pids = set(_game_pids(int(appid)))
    wins = _main_windows(pids)
    if not wins:
        return False
    hwnd = wins[0]
    if _u32.IsIconic(hwnd):
        _u32.ShowWindow(hwnd, 9)  # SW_RESTORE
    fg = _u32.GetForegroundWindow()
    me = _k32.GetCurrentThreadId()
    other = _u32.GetWindowThreadProcessId(fg, None) if fg else 0
    attached = bool(other and other != me and _u32.AttachThreadInput(me, other, True))
    try:
        _u32.keybd_event(0x12, 0, 0, None)  # Alt down
        _u32.keybd_event(0x12, 0, 2, None)  # Alt up
        _u32.BringWindowToTop(hwnd)
        _u32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            _u32.AttachThreadInput(me, other, False)
    return _u32.GetForegroundWindow() == hwnd


def paused():
    with _lock:
        return sorted(_paused.keys())


def resume_all():
    for appid in list(paused()):
        try:
            resume(appid)
        except Exception:
            pass

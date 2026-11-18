"""Windows audio for Guided Windows (1.5.1): Steam on Windows has no SteamClient.System.Audio, so quick settings had no
volume, microphone or device choice there. This talks to Windows Core Audio directly (COM through ctypes, no extra
packages): list playback / recording endpoints with their volume, set an endpoint's volume, make one the default device.

Endpoints are identified by their Windows endpoint id string. Only meaningful on Windows; elsewhere every call reports
"unavailable".
"""
import ctypes
import sys
import uuid

_WIN = sys.platform == "win32"

if _WIN:
    from ctypes import POINTER, WINFUNCTYPE, byref, c_float, c_uint, c_ulong, c_ushort, c_void_p, c_wchar_p, wintypes

    class _GUID(ctypes.Structure):
        _fields_ = [("b", ctypes.c_ubyte * 16)]

    def _guid(text):
        g = _GUID()
        ctypes.memmove(g.b, uuid.UUID(text).bytes_le, 16)
        return g

    class _PROPERTYKEY(ctypes.Structure):
        _fields_ = [("fmtid", _GUID), ("pid", wintypes.DWORD)]

    class _PROPVARIANT(ctypes.Structure):
        # 24 bytes on x64: vt + 3 reserved words, then the 16-byte union (a string pointer for VT_LPWSTR)
        _fields_ = [("vt", c_ushort), ("r1", c_ushort), ("r2", c_ushort), ("r3", c_ushort), ("p", c_void_p), ("p2", c_void_p)]

    _CLSID_MMDeviceEnumerator = _guid("BCDE0395-E52F-467C-8E3D-C4579291692E")
    _IID_IMMDeviceEnumerator = _guid("A95664D2-9614-4F35-A746-DE8DB63617E6")
    _IID_IAudioEndpointVolume = _guid("5CDF2C82-841E-4546-9722-0CF74078229A")
    _CLSID_PolicyConfig = _guid("870AF99C-171D-4F9E-AF0D-E63DF40C2BC9")
    _IID_IPolicyConfig = _guid("F8679F50-850A-41CF-9C72-430F290290C8")
    _PKEY_FriendlyName = _PROPERTYKEY(_guid("A45C254E-DF1C-4EFD-8020-67D146A850E0"), 14)
    _CLSCTX_ALL = 23
    _RENDER, _CAPTURE = 0, 1
    _ACTIVE = 1
    _VT_LPWSTR = 31

    _ole32 = ctypes.OleDLL("ole32")
    _ole32.CoTaskMemFree.restype = None
    _ole32.CoTaskMemFree.argtypes = [c_void_p]

    def _method(obj, index, *argtypes):
        vtable = ctypes.cast(obj, POINTER(POINTER(c_void_p))).contents
        return WINFUNCTYPE(ctypes.HRESULT, c_void_p, *argtypes)(vtable[index])

    def _release(obj):
        if obj:
            vtable = ctypes.cast(obj, POINTER(POINTER(c_void_p))).contents
            WINFUNCTYPE(c_ulong, c_void_p)(vtable[2])(obj)

    class _Com:
        """CoInitialize for the calling (worker) thread, undone again if this call did it."""

        def __enter__(self):
            self.owned = False
            try:
                _ole32.CoInitializeEx(None, 0)  # COINIT_MULTITHREADED; S_FALSE (already) also succeeds
                self.owned = True
            except OSError:
                pass  # RPC_E_CHANGED_MODE: the thread already has COM in another mode - usable as it is
            return self

        def __exit__(self, *exc):
            if self.owned:
                _ole32.CoUninitialize()

    def _enumerator():
        en = c_void_p()
        _ole32.CoCreateInstance(byref(_CLSID_MMDeviceEnumerator), None, _CLSCTX_ALL, byref(_IID_IMMDeviceEnumerator), byref(en))
        return en

    def _device_id(dev):
        raw = c_void_p()
        _method(dev, 5, POINTER(c_void_p))(dev, byref(raw))
        try:
            return ctypes.wstring_at(raw.value)
        finally:
            _ole32.CoTaskMemFree(raw)

    def _device_name(dev):
        store = c_void_p()
        _method(dev, 4, wintypes.DWORD, POINTER(c_void_p))(dev, 0, byref(store))  # STGM_READ
        try:
            pv = _PROPVARIANT()
            _method(store, 5, POINTER(_PROPERTYKEY), POINTER(_PROPVARIANT))(store, byref(_PKEY_FriendlyName), byref(pv))
            try:
                return ctypes.wstring_at(pv.p) if pv.vt == _VT_LPWSTR and pv.p else ""
            finally:
                _ole32.PropVariantClear(byref(pv))
        finally:
            _release(store)

    def _endpoint_volume(dev):
        vol = c_void_p()
        _method(dev, 3, POINTER(_GUID), wintypes.DWORD, c_void_p, POINTER(c_void_p))(dev, byref(_IID_IAudioEndpointVolume), _CLSCTX_ALL, None, byref(vol))
        return vol

    def _get_volume(dev):
        vol = _endpoint_volume(dev)
        try:
            level = c_float()
            _method(vol, 9, POINTER(c_float))(vol, byref(level))  # GetMasterVolumeLevelScalar
            return max(0.0, min(1.0, float(level.value)))
        finally:
            _release(vol)

    def _default_id(en, flow):
        dev = c_void_p()
        try:
            _method(en, 4, c_uint, c_uint, POINTER(c_void_p))(en, flow, 0, byref(dev))  # eConsole
        except OSError:
            return None  # no device of this kind
        try:
            return _device_id(dev)
        finally:
            _release(dev)

    def _list(en, flow):
        coll = c_void_p()
        _method(en, 3, c_uint, wintypes.DWORD, POINTER(c_void_p))(en, flow, _ACTIVE, byref(coll))
        out = []
        try:
            count = c_uint()
            _method(coll, 3, POINTER(c_uint))(coll, byref(count))
            for i in range(count.value):
                dev = c_void_p()
                _method(coll, 4, c_uint, POINTER(c_void_p))(coll, i, byref(dev))
                try:
                    try:
                        volume = _get_volume(dev)
                    except OSError:
                        volume = None
                    out.append({"id": _device_id(dev), "name": _device_name(dev) or "Audio device", "flow": "out" if flow == _RENDER else "in", "volume": volume})
                finally:
                    _release(dev)
        finally:
            _release(coll)
        return out

    def _with_device(endpoint_id, fn):
        en = _enumerator()
        try:
            dev = c_void_p()
            _method(en, 5, c_wchar_p, POINTER(c_void_p))(en, endpoint_id, byref(dev))  # GetDevice
            try:
                return fn(dev)
            finally:
                _release(dev)
        finally:
            _release(en)


def devices():
    """{"available": bool, "devices": [{"id","name","flow": "out"|"in","volume": 0..1|None}], "defaultOut", "defaultIn"}"""
    if not _WIN:
        return {"available": False, "devices": [], "defaultOut": None, "defaultIn": None}
    with _Com():
        en = _enumerator()
        try:
            return {"available": True, "devices": _list(en, _RENDER) + _list(en, _CAPTURE),
                    "defaultOut": _default_id(en, _RENDER), "defaultIn": _default_id(en, _CAPTURE)}
        finally:
            _release(en)


def set_volume(endpoint_id, value):
    """Set an endpoint's master volume (0..1). Returns the volume now in effect."""
    if not _WIN:
        return None
    value = max(0.0, min(1.0, float(value)))

    def apply(dev):
        vol = _endpoint_volume(dev)
        try:
            _method(vol, 7, c_float, c_void_p)(vol, c_float(value), None)  # SetMasterVolumeLevelScalar
        finally:
            _release(vol)
        return _get_volume(dev)

    with _Com():
        return _with_device(str(endpoint_id), apply)


def set_default(endpoint_id):
    """Make an endpoint the default device for every role (console, multimedia, communications) - like the
    Windows sound settings. Uses the (undocumented but long-stable) IPolicyConfig interface."""
    if not _WIN:
        return False
    with _Com():
        pc = c_void_p()
        _ole32.CoCreateInstance(byref(_CLSID_PolicyConfig), None, _CLSCTX_ALL, byref(_IID_IPolicyConfig), byref(pc))
        try:
            for role in (0, 1, 2):
                _method(pc, 13, c_wchar_p, c_uint)(pc, str(endpoint_id), role)  # SetDefaultEndpoint
        finally:
            _release(pc)
    return True

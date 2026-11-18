"""Discord's own Go Live quality inside Steamcord's Discord window (Vesktop, debug port 39223). Steamcord starts a share
in Game Mode without Discord's Go Live dialog, so Discord streams with its stored setting (720p / 30 by default); this
sets that setting the way the dialog does (ApplicationStreamingSettingsStore via STREAM_UPDATE_SETTINGS). Steamcord's
files are not touched; the user agreed to this (2026-11-18)."""
import json

from guided import media

VESKTOP_CDP = 39223


def set_quality(resolution: int, fps: int) -> dict:
    if resolution not in (0, 480, 720, 1080) or fps not in (15, 30, 60):
        return {"ok": False, "error": "bad-value"}
    js = ("(() => { const WP = window.Vencord?.Webpack; if (!WP) return null; "
          "const D = WP.Common?.FluxDispatcher; const s = WP.findStore('ApplicationStreamingSettingsStore'); if (!D || !s) return null; "
          f"D.dispatch({{ type: 'STREAM_UPDATE_SETTINGS', preset: 3, resolution: {resolution}, frameRate: {fps} }}); "
          "return JSON.stringify(s.getState()); })()")
    raw = media.cdp_eval(VESKTOP_CDP, lambda t: "discord.com" in t.get("url", "") and t.get("type") == "page", js, 8)
    return {"ok": raw is not None, "state": json.loads(raw) if raw else None}

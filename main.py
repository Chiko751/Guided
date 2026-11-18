import asyncio
import datetime
import os
import shutil

import decky

from guided import accounts, media, power
from guided.bluetooth import list_devices, read_controllers, set_connected
from guided.frost.service import FrostService
from guided.heroic import HeroicLibrary, heroic_cache_dirs
from guided.home_errors import FILE_NAME, append_log, start_entry
from guided.kv import KvStore
from guided.store_lookup import RegistryCache, key_for_appid, store_for_appid
from guided import wifi
from guided import winaudio
from guided import winpause
from guided import gamevol
from guided import discordq

DATA_PATH = os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "data.json")
# Guided 1.0: the plugin was called Guided360 - take its settings over once (before the store is first read)
OLD_SETTINGS = ("Guided", "Guided360", "Guided360-Clean")  # "Guided": the Windows build takes over a Guided install


def _take_over_old_settings():
    if os.path.exists(DATA_PATH):
        return None
    parent = os.path.dirname(os.path.normpath(decky.DECKY_PLUGIN_SETTINGS_DIR))
    for name in OLD_SETTINGS:
        old = os.path.join(parent, name, "data.json")
        if os.path.isfile(old):
            try:
                os.makedirs(decky.DECKY_PLUGIN_SETTINGS_DIR, exist_ok=True)
                shutil.copy2(old, DATA_PATH)
                return name
            except OSError:
                return None
    return None


TOOK_OVER_FROM = _take_over_old_settings()
KV = KvStore(DATA_PATH)
REGISTRY = RegistryCache(
    os.path.join(decky.DECKY_USER_HOME, ".local", "share", "unifideck", "shortcuts_registry.json")
)
HEROIC = HeroicLibrary(heroic_cache_dirs(decky.DECKY_USER_HOME))


class Plugin:
    def _frost_service(self):
        if not getattr(self, "_frost", None):
            self._frost = FrostService(decky.DECKY_USER_HOME, os.path.dirname(os.path.abspath(__file__)))
        return self._frost

    async def frost_prepare(self, request_id: str, frame):
        return await self._frost_service().prepare(request_id, frame)

    async def frost_environment(self):
        return await self._frost_service().environment()

    async def frost_present(self, request_id: str, frame):
        return await self._frost_service().present(request_id, frame)

    async def frost_activate(self, request_id: str, key: str, sequence: int, frame):
        return await self._frost_service().activate(request_id, key, sequence, frame)

    async def frost_update(self, token: str, sequence: int, frame):
        return await self._frost_service().update(token, sequence, frame)

    async def frost_renew(self, token: str):
        return await self._frost_service().renew(token)

    async def frost_release(self, token: str):
        await self._frost_service().release(token)

    async def frost_cancel(self, request_id: str):
        await self._frost_service().cancel(request_id)

    async def kv_get(self, key: str):
        return KV.get(key)

    async def kv_set(self, key: str, value) -> None:
        KV.set(key, value)

    async def kv_delete(self, key: str) -> None:
        KV.delete(key)

    async def kv_delete_prefix(self, prefix: str) -> int:
        return KV.delete_prefix(prefix)

    async def get_store(self, appid: int):
        try:
            return store_for_appid(REGISTRY.get(), int(appid))
        except Exception:
            decky.logger.exception("[guided] get_store failed")
            return None

    async def get_unifideck_key(self, appid: int):
        try:
            return key_for_appid(REGISTRY.get(), int(appid))
        except Exception:
            decky.logger.exception("[guided] get_unifideck_key failed")
            return None

    async def get_heroic_description(self, runner: str, app_name: str):
        try:
            return HEROIC.description(str(runner), str(app_name))
        except Exception:
            decky.logger.exception("[guided] get_heroic_description failed")
            return None

    async def get_controller_batteries(self):
        try:
            return await asyncio.to_thread(read_controllers, log=lambda reason: decky.logger.warning(f"[guided] controller batteries: {reason}"))
        except Exception:
            decky.logger.exception("[guided] get_controller_batteries failed")
            return []

    async def list_bluetooth_devices(self, scan: bool = False):
        try:
            return await asyncio.to_thread(list_devices, 6 if scan else 0, log=lambda reason: decky.logger.warning(f"[guided] bluetooth: {reason}"))
        except Exception:
            decky.logger.exception("[guided] list_bluetooth_devices failed")
            return []

    async def set_bluetooth_connected(self, mac: str, connect: bool):
        try:
            return await asyncio.to_thread(set_connected, str(mac), bool(connect), log=lambda reason: decky.logger.warning(f"[guided] bluetooth: {reason}"))
        except Exception:
            decky.logger.exception("[guided] set_bluetooth_connected failed")
            return False

    async def list_wifi_networks(self, rescan: bool = False):
        # {"state": on|off|missing, "networks": [{"ssid","signal","secure","connected","known"}]}
        try:
            return await asyncio.to_thread(wifi.list_networks, bool(rescan), log=lambda reason: decky.logger.warning(f"[guided] wifi: {reason}"))
        except Exception:
            decky.logger.exception("[guided] list_wifi_networks failed")
            return {"state": "missing", "networks": []}

    async def connect_wifi(self, ssid: str, password: str = ""):
        try:
            return await asyncio.to_thread(wifi.connect, str(ssid), str(password) if password else None, log=lambda reason: decky.logger.warning(f"[guided] wifi: {reason}"))
        except Exception:
            decky.logger.exception("[guided] connect_wifi failed")
            return {"ok": False, "reason": "failed"}

    async def disconnect_wifi(self, ssid: str):
        try:
            return await asyncio.to_thread(wifi.disconnect, str(ssid), log=lambda reason: decky.logger.warning(f"[guided] wifi: {reason}"))
        except Exception:
            decky.logger.exception("[guided] disconnect_wifi failed")
            return False

    async def list_steam_accounts(self):
        # [{"steamId", "account", "persona", "mostRecent"}] from Steam's loginusers.vdf.
        try:
            return await asyncio.to_thread(accounts.list_accounts, decky.DECKY_USER_HOME)
        except Exception:
            decky.logger.exception("[guided] list_steam_accounts failed")
            return []

    async def switch_steam_account(self, account: str):
        # Shuts Steam down, sets AutoLoginUser once Steam has exited; Steam then starts as that account.
        try:
            return await asyncio.to_thread(accounts.switch_account, decky.DECKY_USER_HOME, getattr(decky, "DECKY_USER", None), str(account))
        except Exception:
            decky.logger.exception("[guided] switch_steam_account failed")
            return False

    async def power_capabilities(self):
        try:
            return power.capabilities()
        except Exception:
            return ["sleep", "restart", "shutdown"]

    async def power_action(self, action: str):
        try:
            return await asyncio.to_thread(power.run, str(action), lambda reason: decky.logger.warning(f"[guided] power: {reason}"))
        except Exception:
            decky.logger.exception("[guided] power_action failed")
            return False

    # 1.5.1: Windows audio (Steam on Windows has no SteamClient.System.Audio) - devices with volume, volume, default device
    async def win_audio_devices(self):
        try:
            return await asyncio.to_thread(winaudio.devices)
        except Exception:
            decky.logger.exception("[guided] win_audio_devices failed")
            return {"available": False, "devices": [], "defaultOut": None, "defaultIn": None}

    async def discord_stream_quality(self, resolution: int, fps: int):
        try:
            return await asyncio.to_thread(discordq.set_quality, int(resolution), int(fps))
        except Exception:
            decky.logger.exception("[guided] discord_stream_quality failed")
            return {"ok": False}

    async def game_volume(self, app_id: str):
        try:
            return await asyncio.to_thread(gamevol.get, str(app_id))
        except Exception:
            decky.logger.exception("[guided] game_volume failed")
            return {"ok": False}

    async def game_volume_set(self, app_id: str, value: int):
        try:
            return await asyncio.to_thread(gamevol.set_volume, str(app_id), int(value))
        except Exception:
            decky.logger.exception("[guided] game_volume_set failed")
            return {"ok": False}

    async def win_audio_volume(self, endpoint_id: str, value: float):
        try:
            return await asyncio.to_thread(winaudio.set_volume, str(endpoint_id), float(value))
        except Exception:
            decky.logger.exception("[guided] win_audio_volume failed")
            return None

    async def win_audio_default(self, endpoint_id: str):
        try:
            return await asyncio.to_thread(winaudio.set_default, str(endpoint_id))
        except Exception:
            decky.logger.exception("[guided] win_audio_default failed")
            return False

    # Guided Windows: pause / resume games (PauseGames for Windows) - NtSuspendProcess on the game's processes
    async def win_pause(self, appid: int):
        try:
            return await asyncio.to_thread(winpause.pause, int(appid))
        except Exception:
            decky.logger.exception("[guided] win_pause failed")
            return {"ok": False, "paused": 0, "failed": 0, "reason": "error"}

    async def win_resume(self, appid: int):
        try:
            return await asyncio.to_thread(winpause.resume, int(appid))
        except Exception:
            decky.logger.exception("[guided] win_resume failed")
            return {"ok": False, "resumed": 0}

    async def win_raise(self, appid: int):
        try:
            return await asyncio.to_thread(winpause.raise_app, int(appid))
        except Exception:
            decky.logger.exception("[guided] win_raise failed")
            return False

    async def win_is_foreground(self, appid: int):
        try:
            return await asyncio.to_thread(winpause.is_foreground, int(appid))
        except Exception:
            return None

    async def win_paused(self):
        try:
            return winpause.paused()
        except Exception:
            return []

    async def _media(self, fn, *args):
        try:
            return await asyncio.to_thread(fn, *args)
        except Exception as e:
            decky.logger.warning(f"[guided] media {getattr(fn, '__name__', fn)}: {e}")
            return {"ok": False, "error": str(e)[:200]}

    async def media_state(self, source: str):
        return await self._media(media.spotify_state if source == "spotify" else media.yt_state)

    async def media_library(self, source: str):
        return await self._media(media.spotify_library if source == "spotify" else media.yt_library)

    async def media_tracks(self, source: str, uri: str):
        return await self._media(media.spotify_tracks if source == "spotify" else media.yt_tracks, str(uri or ""))

    async def media_search(self, source: str, term: str):
        return await self._media(media.spotify_search if source == "spotify" else media.yt_search, str(term or ""))

    async def media_control(self, source: str, action: str, uri: str = ""):
        fn = media.spotify_control if source == "spotify" else media.yt_control
        if action != "volume":
            decky.logger.info(f"[guided] media {source} {action} {str(uri or '')[:60]}")
        return await self._media(fn, str(action), str(uri or ""))

    async def media_spotify_start(self, restart: bool = False):
        return await self._media(media.spotify_start, bool(restart))

    async def log_home_error(self, entry: str) -> None:
        try:
            append_log(decky.DECKY_PLUGIN_LOG_DIR, f"v{decky.DECKY_PLUGIN_VERSION} {entry}"[:8000])
        except Exception:
            decky.logger.exception("[guided] log_home_error failed")

    async def make_executable(self, path: str):
        """'Add a game' (1.3.24): AppImages / scripts / binaries must be executable for Steam to start them. Only regular
        files below the user's home or /run/media / /mnt (external drives); adds the user's execute bit."""
        try:
            real = os.path.realpath(str(path))
            home = os.path.realpath(decky.DECKY_USER_HOME)
            if not os.path.isfile(real) or not any(real.startswith(p + os.sep) for p in (home, "/run/media", "/mnt", "/media")):
                return False
            mode = os.stat(real).st_mode
            os.chmod(real, mode | 0o100)
            return True
        except OSError:
            return False

    async def takeover_status(self):
        """Old Guided360 may be removed once this plugin has its settings (taken over or its own)."""
        return {"from": TOOK_OVER_FROM, "ready": os.path.exists(DATA_PATH) or not any(
            os.path.isfile(os.path.join(os.path.dirname(os.path.normpath(decky.DECKY_PLUGIN_SETTINGS_DIR)), n, "data.json")) for n in OLD_SETTINGS)}

    async def _main(self):
        decky.logger.info(f"[guided] backend started{f' (settings taken over from {TOOK_OVER_FROM})' if TOOK_OVER_FROM else ''}")
        try:
            now = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
            path = os.path.join(decky.DECKY_PLUGIN_LOG_DIR, FILE_NAME)
            append_log(decky.DECKY_PLUGIN_LOG_DIR, start_entry(decky.DECKY_PLUGIN_VERSION, now, path))
        except Exception:
            decky.logger.exception("[guided] start-up log entry failed")
        # Guided Windows: resume games a previous backend left paused (crash, Decky restart)
        try:
            winpause.set_state_file(os.path.join(decky.DECKY_PLUGIN_SETTINGS_DIR, "paused-games.json"))
            n = await asyncio.to_thread(winpause.recover)
            if n:
                decky.logger.info(f"[guided] resumed {n} game process(es) left paused")
        except Exception:
            decky.logger.exception("[guided] pause recovery failed")

    async def _unload(self):
        try:
            await asyncio.to_thread(winpause.resume_all)
        except Exception:
            decky.logger.exception("[guided] resuming paused games failed")
        if getattr(self, "_frost", None):
            await self._frost.close()
        decky.logger.info("[guided] backend stopped")

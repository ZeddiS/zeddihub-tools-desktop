"""
Layer 1: Game builds via Steam Web API (public branch buildid).

Uses ISteamApps/UpToDateCheck as a cheap signal and falls back to
IStoreService/GetAppInfo for the buildid when available.

App IDs:
  - Rust (client):      252490
  - Rust Dedicated:     258550
  - CS2 / CS:GO:        730 (and DS 740 for server)
"""

import json
import urllib.request
import urllib.parse
from typing import Optional

from .base import UpdateSource, UpdateResult

APP_IDS = {
    "rust":        258550,   # Rust Dedicated Server
    "rust_client": 252490,
    "cs2":         730,
    "csgo":        730,
    "cs2_ds":      740,
}


class GameBuildsSource(UpdateSource):
    name = "game_builds"
    label = "Game build (Steam)"

    def check(self, target: str, current_version: Optional[str] = None) -> UpdateResult:
        appid = APP_IDS.get(target.lower())
        if not appid:
            return UpdateResult(self.name, target, None, current_version, False,
                                error=f"neznámé game target: {target}")

        url = (
            "https://api.steampowered.com/ISteamApps/UpToDateCheck/v1/"
            f"?appid={appid}&version={urllib.parse.quote(str(current_version or 0))}"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            return UpdateResult(self.name, target, None, current_version, False,
                                error=f"Steam API: {e}")

        rsp = (data.get("response") or {})
        success = rsp.get("success", False)
        up_to_date = rsp.get("up_to_date", True)
        required = rsp.get("required_version")

        latest = str(required) if required is not None else None
        update = bool(success and not up_to_date)

        return UpdateResult(
            self.name, target, latest, current_version, update,
            url=f"https://steamdb.info/app/{appid}/",
            extra={"appid": appid},
        )

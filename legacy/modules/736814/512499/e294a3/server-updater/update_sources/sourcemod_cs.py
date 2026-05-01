"""
Layer 3: MetaMod + SourceMod (+ CounterStrikeSharp) for CS2 / CS:GO.

- MetaMod:  https://www.metamodsource.net/mmsdrop/2.0/mmsource-latest-version
- SourceMod branches: https://sm.alliedmods.net/smdrop/1.13/sourcemod-latest
- CSSharp (CS2): GitHub Releases latest tag
"""

import json
import urllib.request
from typing import Optional

from .base import UpdateSource, UpdateResult

METAMOD_URL   = "https://mms.alliedmods.net/mmsdrop/2.0/mmsource-latest-linux"
SOURCEMOD_URL = "https://sm.alliedmods.net/smdrop/1.13/sourcemod-latest-linux"
CSSHARP_API   = "https://api.github.com/repos/roflmuffin/CounterStrikeSharp/releases/latest"


def _fetch_text(url: str, timeout: int = 8) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode().strip()


def _fetch_json(url: str, timeout: int = 8) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": "ZeddiHubTools",
                                               "Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class SourceModCSSource(UpdateSource):
    name = "sourcemod_cs"
    label = "MetaMod / SourceMod / CSSharp"

    def check(self, target: str, current_version: Optional[str] = None) -> UpdateResult:
        target = target.lower()
        try:
            if target == "metamod":
                latest = _fetch_text(METAMOD_URL)
                return UpdateResult(self.name, "metamod", latest, current_version,
                                    self._compare(current_version, latest),
                                    url="https://www.metamodsource.net/downloads.php")
            if target == "sourcemod":
                latest = _fetch_text(SOURCEMOD_URL)
                return UpdateResult(self.name, "sourcemod", latest, current_version,
                                    self._compare(current_version, latest),
                                    url="https://www.sourcemod.net/downloads.php")
            if target in ("cssharp", "counterstrikesharp"):
                data = _fetch_json(CSSHARP_API)
                latest = data.get("tag_name")
                return UpdateResult(self.name, "cssharp", latest, current_version,
                                    self._compare(current_version, latest),
                                    url=data.get("html_url"))
            return UpdateResult(self.name, target, None, current_version, False,
                                error=f"neznámé target: {target}")
        except Exception as e:
            return UpdateResult(self.name, target, None, current_version, False,
                                error=str(e))

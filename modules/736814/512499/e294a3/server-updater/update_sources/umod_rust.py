"""
Layer 2: uMod / Oxide for Rust — latest published Oxide.Rust version.

Uses the uMod.org game endpoint which serves JSON metadata including
the latest release version + download URL.
"""

import json
import urllib.request
from typing import Optional

from .base import UpdateSource, UpdateResult

UMOD_API = "https://umod.org/games/rust.json"


class UmodRustSource(UpdateSource):
    name = "umod_rust"
    label = "Oxide / uMod (Rust)"

    def check(self, target: str = "rust", current_version: Optional[str] = None) -> UpdateResult:
        try:
            req = urllib.request.Request(UMOD_API, headers={"User-Agent": "ZeddiHubTools"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            return UpdateResult(self.name, "oxide", None, current_version, False,
                                error=f"uMod API: {e}")

        latest = data.get("latest_release_version") or data.get("latest_release") \
                 or data.get("version")
        url = data.get("latest_release_url") or "https://umod.org/games/rust"
        update = self._compare(current_version, latest)

        return UpdateResult(self.name, "oxide", latest, current_version, update, url=url)

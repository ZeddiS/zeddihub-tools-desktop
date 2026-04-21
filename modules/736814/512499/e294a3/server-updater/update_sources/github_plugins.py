"""
Layer 4: Per-plugin updates via GitHub Releases.

target = "owner/repo".  Returns latest tag_name + asset URL.
"""

import json
import urllib.request
from typing import Optional

from .base import UpdateSource, UpdateResult


class GitHubPluginsSource(UpdateSource):
    name = "github_plugins"
    label = "GitHub Releases (plugin)"

    def check(self, target: str, current_version: Optional[str] = None) -> UpdateResult:
        if not target or "/" not in target:
            return UpdateResult(self.name, target or "?", None, current_version, False,
                                error='target musí být "owner/repo"')
        url = f"https://api.github.com/repos/{target}/releases/latest"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "ZeddiHubTools",
                "Accept": "application/vnd.github+json",
            })
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
        except Exception as e:
            return UpdateResult(self.name, target, None, current_version, False,
                                error=f"GitHub API: {e}")

        latest = data.get("tag_name")
        assets = data.get("assets") or []
        asset_url = assets[0].get("browser_download_url") if assets else None

        return UpdateResult(
            self.name, target, latest, current_version,
            self._compare(current_version, latest),
            url=data.get("html_url"),
            extra={"asset_url": asset_url, "published_at": data.get("published_at")},
        )

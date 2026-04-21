"""
Base interface for Server Updater sources.

Each source is a remote-monitoring plugin that reports the latest known
version for some upstream artifact (game build, mod framework, plugin).
"""

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class UpdateResult:
    source: str                     # e.g. "game_builds"
    target: str                     # e.g. "rust", "cs2", "oxide", "owner/repo"
    latest_version: Optional[str]   # human-readable version/tag/buildid
    current_version: Optional[str]  # locally known version (or None)
    update_available: bool
    url: Optional[str] = None       # changelog / release page
    error: Optional[str] = None
    extra: dict = field(default_factory=dict)


class UpdateSource:
    """Abstract interface. Implementations must override check()."""
    name: str = "abstract"
    label: str = "Abstract source"

    def check(self, target: str, current_version: Optional[str] = None) -> UpdateResult:
        """Fetch latest upstream version and compare against current_version."""
        raise NotImplementedError

    @staticmethod
    def _compare(current: Optional[str], latest: Optional[str]) -> bool:
        """True when latest != current (and both present)."""
        if not latest or not current:
            return False
        return str(latest).strip() != str(current).strip()

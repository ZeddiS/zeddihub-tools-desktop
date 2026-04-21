"""
ZeddiHub Tools Desktop - Single source of truth for the application version.

Any module that needs to know the current version MUST import APP_VERSION from here.
When bumping the version, only this file needs to change — updater.py and telemetry.py
pull their constants from this module.

NOTE: version.json at the repo root and webhosting/data/version.json are kept as
fallbacks for offline clients and the legacy updater path. They are rewritten by the
release helper bat (zeddihub.bat) at tag time.
"""

APP_VERSION = "1.7.3"
APP_NAME = "ZeddiHub Tools Desktop"
GITHUB_OWNER = "ZeddiS"
GITHUB_REPO = "zeddihub-tools-desktop"


def user_agent() -> str:
    """Standard HTTP User-Agent used by updater, telemetry and GitHub API clients."""
    return f"ZeddiHubTools/{APP_VERSION}"

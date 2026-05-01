"""
Server Updater — modular update detection sources.

Each source implements the UpdateSource interface (check_latest + compare_current).
Sources are registered in SOURCES and consumed by gui.panels.server_updater.
"""

from .base import UpdateSource, UpdateResult
from .game_builds import GameBuildsSource
from .umod_rust import UmodRustSource
from .sourcemod_cs import SourceModCSSource
from .github_plugins import GitHubPluginsSource

SOURCES = {
    "game_builds":     GameBuildsSource(),
    "umod_rust":       UmodRustSource(),
    "sourcemod_cs":    SourceModCSSource(),
    "github_plugins":  GitHubPluginsSource(),
}

__all__ = ["UpdateSource", "UpdateResult", "SOURCES"]

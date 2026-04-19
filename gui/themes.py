"""
ZeddiHub Tools - Color theme system per game.

v1.9.0 - "Win11 Dark Gaming" identity:
* Windows 11 inspired deep-black backgrounds with subtle cool undertone.
* Primary blue (#0078D4) mirroring Windows 11 accent.
* Gaming purple (#6B46C1) as secondary flair accent.
* Layered surfaces: bg -> sidebar_bg -> content_bg -> card_bg -> card_hover -> glass.
* Added keys (with fallbacks in gui/widgets.py):
    - accent_soft, text_muted, card_hover, glass, outline, shadow (already present in v1.8)
* Per-game themes retain their signature hues (cs2 orange, csgo blue, rust red-brown)
  but adopt the new depth structure from the default Win11 Dark Gaming theme.

Back-compat: every pre-existing theme key is preserved. New keys have graceful
fallbacks in widgets.py so older panels that still read the raw dict keep working.
"""

GAME_THEMES = {
    "default": {
        # Win11 Dark Gaming palette
        "primary": "#0078D4",
        "primary_hover": "#1a8cdd",
        "bg": "#0a0a0f",
        "sidebar_bg": "#0f0f17",
        "header_bg": "#0d0d16",
        "content_bg": "#111119",
        "card_bg": "#1a1a26",
        "card_hover": "#232333",
        "glass": "#1e1e2c",
        "secondary": "#1a8cdd",
        "border": "#2a2a3a",
        "outline": "#3a3a4a",
        "text": "#e8e8f0",
        "text_dim": "#8080a0",
        "text_dark": "#0a0a0f",
        "text_muted": "#5a5a78",
        "success": "#22c55e",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "accent": "#6B46C1",
        "accent_soft": "#2a1f4f",
        "shadow": "#050509",
        "button_fg": "#ffffff",
        "name": "Default",
        # Light mode overrides (Win11 Light styling)
        "light": {
            "bg": "#f5f5f7",
            "sidebar_bg": "#ebebf0",
            "header_bg": "#e4e4ec",
            "content_bg": "#f5f5f7",
            "card_bg": "#ffffff",
            "card_hover": "#f0f0f5",
            "glass": "#f8f8fc",
            "secondary": "#0078D4",
            "border": "#d0d0e0",
            "outline": "#b8b8c8",
            "text": "#0a0a0f",
            "text_dim": "#5a5a78",
            "text_dark": "#b8b8c8",
            "text_muted": "#7a7a90",
            "accent_soft": "#e6ddf5",
            "shadow": "#d8d8e0",
        },
    },
    "cs2": {
        # CS2 orange on Win11 Dark Gaming base
        "primary": "#f5b623",
        "primary_hover": "#e6a714",
        "bg": "#0a0a0f",
        "sidebar_bg": "#0f0f17",
        "header_bg": "#0d0d16",
        "content_bg": "#111119",
        "card_bg": "#1a1a26",
        "card_hover": "#232333",
        "glass": "#1e1e2c",
        "secondary": "#f5b623",
        "border": "#2a2a3a",
        "outline": "#3a3a4a",
        "text": "#e8e8f0",
        "text_dim": "#8080a0",
        "text_dark": "#0a0a0f",
        "text_muted": "#5a5a78",
        "success": "#22c55e",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "accent": "#6B46C1",
        "accent_soft": "#3a2c10",
        "shadow": "#050509",
        "button_fg": "#ffffff",
        "name": "Counter-Strike 2",
        "light": {
            "bg": "#f5f5f7",
            "sidebar_bg": "#ebebf0",
            "header_bg": "#e4e4ec",
            "content_bg": "#f5f5f7",
            "card_bg": "#ffffff",
            "card_hover": "#fbf3de",
            "glass": "#fef8e8",
            "secondary": "#f5b623",
            "border": "#d0d0e0",
            "outline": "#b8b8c8",
            "text": "#0a0a0f",
            "text_dim": "#5a5a78",
            "text_dark": "#b8b8c8",
            "text_muted": "#7a7a90",
            "accent_soft": "#fbe8be",
            "shadow": "#d8d8e0",
        },
    },
    "csgo": {
        # CS:GO blue on Win11 Dark Gaming base
        "primary": "#3399ff",
        "primary_hover": "#1f85eb",
        "bg": "#0a0a0f",
        "sidebar_bg": "#0f0f17",
        "header_bg": "#0d0d16",
        "content_bg": "#111119",
        "card_bg": "#1a1a26",
        "card_hover": "#232333",
        "glass": "#1e1e2c",
        "secondary": "#3399ff",
        "border": "#2a2a3a",
        "outline": "#3a3a4a",
        "text": "#e8e8f0",
        "text_dim": "#8080a0",
        "text_dark": "#0a0a0f",
        "text_muted": "#5a5a78",
        "success": "#22c55e",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "accent": "#6B46C1",
        "accent_soft": "#0f2238",
        "shadow": "#050509",
        "button_fg": "#ffffff",
        "name": "CS:GO",
        "light": {
            "bg": "#f5f5f7",
            "sidebar_bg": "#ebebf0",
            "header_bg": "#e4e4ec",
            "content_bg": "#f5f5f7",
            "card_bg": "#ffffff",
            "card_hover": "#e8f1ff",
            "glass": "#f2f7ff",
            "secondary": "#3399ff",
            "border": "#d0d0e0",
            "outline": "#b8b8c8",
            "text": "#0a0a0f",
            "text_dim": "#5a5a78",
            "text_dark": "#b8b8c8",
            "text_muted": "#7a7a90",
            "accent_soft": "#d2e0fa",
            "shadow": "#d8d8e0",
        },
    },
    "rust": {
        # Rust red-brown on Win11 Dark Gaming base
        "primary": "#cd5a3a",
        "primary_hover": "#b94a2c",
        "bg": "#0a0a0f",
        "sidebar_bg": "#0f0f17",
        "header_bg": "#0d0d16",
        "content_bg": "#111119",
        "card_bg": "#1a1a26",
        "card_hover": "#232333",
        "glass": "#1e1e2c",
        "secondary": "#cd5a3a",
        "border": "#2a2a3a",
        "outline": "#3a3a4a",
        "text": "#e8e8f0",
        "text_dim": "#8080a0",
        "text_dark": "#0a0a0f",
        "text_muted": "#5a5a78",
        "success": "#22c55e",
        "error": "#ef4444",
        "warning": "#f59e0b",
        "accent": "#6B46C1",
        "accent_soft": "#3a2010",
        "shadow": "#050509",
        "button_fg": "#ffffff",
        "name": "Rust",
        "light": {
            "bg": "#f5f5f7",
            "sidebar_bg": "#ebebf0",
            "header_bg": "#e4e4ec",
            "content_bg": "#f5f5f7",
            "card_bg": "#ffffff",
            "card_hover": "#fbeae2",
            "glass": "#fef2ec",
            "secondary": "#cd5a3a",
            "border": "#d0d0e0",
            "outline": "#b8b8c8",
            "text": "#0a0a0f",
            "text_dim": "#5a5a78",
            "text_dark": "#b8b8c8",
            "text_muted": "#7a7a90",
            "accent_soft": "#fdd9ba",
            "shadow": "#d8d8e0",
        },
    },
}


def get_theme(game: str, mode: str = None) -> dict:
    base = dict(GAME_THEMES.get(game, GAME_THEMES["default"]))
    if mode == "light":
        light_overrides = base.pop("light", {})
        base.update(light_overrides)
    else:
        base.pop("light", None)
    return base

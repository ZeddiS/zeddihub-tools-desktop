"""
gui/widgets.py - shared widget helpers used across all panels.

Replaces the duplicated ``_label`` / ``_btn`` / ``_section`` / ``_entry_row`` /
``_bool_row`` / ``_dropdown_row`` / ``_stepper_row`` functions previously
copy-pasted into cs2.py, csgo.py, rust.py, etc. (see CLAUDE.md TD-002).

Win11 Dark Gaming styled:
* corner_radius = 8 for entries, 10 for cards and buttons.
* border_color on focus switches to the active accent (primary by default).
* hover glow via fg_color swap (card_hover key).
* All helpers are forgiving: they read optional theme keys through
  :func:`_theme_get` which provides safe fallbacks so panels still work even
  if an older/partial theme dict is passed.

Exported helpers (public API):
    make_label(parent, text, theme, *, size=12, bold=False, color=None)
    make_button(parent, text, command, theme, *, width=180, height=36,
                accent="primary", icon=None)
    make_card(parent, theme, *, title=None, padding=14)
    make_entry(parent, var, theme, *, placeholder=None, width=200,
               on_focus_accent="primary")
    make_stepper(parent, var, theme, *, min_val=0, max_val=999, step=1,
                 width=120)
    make_dropdown(parent, var, values, theme, *, width=180)
    make_tabview(parent, theme, *, height=None)
    make_section_title(parent, text, theme)
    apply_sidebar_active_style(button, theme)
    apply_animated_hover(widget, theme)
"""

from __future__ import annotations

from typing import Any, Callable, Iterable, Optional

import customtkinter as ctk

# ----------------------------------------------------------------------------
# Theme access helpers
# ----------------------------------------------------------------------------

# Safe fallbacks for theme keys that may be missing in older theme dicts.
# Anything not explicitly listed here is looked up with a sensible default in
# :func:`_theme_get` below.
_THEME_FALLBACKS = {
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
}


def _theme_get(theme: dict, key: str, default: Any = None) -> Any:
    """Safely fetch a theme key with multi-level fallback.

    Order of resolution:
      1. theme[key] if present and truthy-ish (i.e., not None).
      2. explicit ``default`` argument if provided.
      3. :data:`_THEME_FALLBACKS` mapping.
      4. finally None.
    """
    if theme:
        val = theme.get(key)
        if val is not None:
            return val
    if default is not None:
        return default
    # text_muted -> text_dim -> text fallback chain
    if key == "text_muted":
        return (
            theme.get("text_dim") if theme else None
        ) or _THEME_FALLBACKS.get("text_muted")
    if key == "card_hover":
        return (
            theme.get("secondary") if theme else None
        ) or _THEME_FALLBACKS.get("card_hover")
    if key == "glass":
        return (
            theme.get("card_bg") if theme else None
        ) or _THEME_FALLBACKS.get("glass")
    if key == "outline":
        return (
            theme.get("border") if theme else None
        ) or _THEME_FALLBACKS.get("outline")
    if key == "accent":
        return (
            theme.get("primary") if theme else None
        ) or _THEME_FALLBACKS.get("accent")
    if key == "accent_soft":
        return (
            theme.get("secondary") if theme else None
        ) or _THEME_FALLBACKS.get("accent_soft")
    return _THEME_FALLBACKS.get(key)


def _accent_color(theme: dict, accent: str) -> str:
    """Map an ``accent`` string ("primary" | "secondary" | "accent" | "danger")
    to the corresponding theme color with graceful fallbacks.
    """
    if accent == "secondary":
        return _theme_get(theme, "secondary")
    if accent == "accent":
        return _theme_get(theme, "accent")
    if accent in ("danger", "error"):
        return _theme_get(theme, "error")
    if accent == "success":
        return _theme_get(theme, "success")
    if accent == "warning":
        return _theme_get(theme, "warning")
    # default
    return _theme_get(theme, "primary")


def _accent_hover(theme: dict, accent: str) -> str:
    """Return a hover color matching the accent (falls back to card_hover)."""
    if accent == "primary":
        return _theme_get(theme, "primary_hover")
    # for other accents just use card_hover for a subtle darken
    return _theme_get(theme, "card_hover")


# ----------------------------------------------------------------------------
# Public widget helpers
# ----------------------------------------------------------------------------

def make_label(
    parent,
    text: str,
    theme: dict,
    *,
    size: int = 12,
    bold: bool = False,
    color: Optional[str] = None,
    **kwargs,
) -> ctk.CTkLabel:
    """Create a standard CTkLabel themed with Win11 Dark Gaming styling."""
    weight = "bold" if bold else "normal"
    fg = color if color is not None else _theme_get(theme, "text")
    return ctk.CTkLabel(
        parent,
        text=text,
        font=ctk.CTkFont(size=size, weight=weight),
        text_color=fg,
        **kwargs,
    )


def make_button(
    parent,
    text: str,
    command: Optional[Callable],
    theme: dict,
    *,
    width: int = 180,
    height: int = 36,
    accent: str = "primary",
    icon: Any = None,
    **kwargs,
) -> ctk.CTkButton:
    """Create a themed CTkButton.

    ``accent`` can be one of ``"primary"``, ``"secondary"``, ``"accent"``,
    ``"danger"``, ``"success"``, ``"warning"`` - it chooses ``fg_color`` from
    the theme.
    """
    fg = _accent_color(theme, accent)
    hover = _accent_hover(theme, accent)
    text_color = _theme_get(theme, "button_fg")
    # For subtle accents on dark bg ensure contrast
    kwargs.setdefault("corner_radius", 10)
    btn = ctk.CTkButton(
        parent,
        text=text,
        command=command,
        width=width,
        height=height,
        fg_color=fg,
        hover_color=hover,
        text_color=text_color,
        image=icon,
        **kwargs,
    )
    return btn


def make_card(
    parent,
    theme: dict,
    *,
    title: Optional[str] = None,
    padding: int = 14,
    **kwargs,
) -> ctk.CTkFrame:
    """Create a card frame with border and optional H3 title label.

    If ``title`` is given the returned frame will already contain the title
    label packed at the top; subsequent children added by the caller will stack
    below it when packed with ``fill="x"``.
    """
    kwargs.setdefault("corner_radius", 10)
    kwargs.setdefault("fg_color", _theme_get(theme, "card_bg"))
    kwargs.setdefault("border_width", 1)
    kwargs.setdefault("border_color", _theme_get(theme, "border"))
    card = ctk.CTkFrame(parent, **kwargs)
    if title:
        lbl = ctk.CTkLabel(
            card,
            text=title,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=_theme_get(theme, "text"),
        )
        lbl.pack(padx=padding, pady=(padding, padding // 2), anchor="w")
    # Note: caller is responsible for further padding; padding arg is exposed
    # for future use (e.g., inner container creation) but kept unused here to
    # avoid forcing a layout mode on the consumer.
    return card


def make_entry(
    parent,
    var,
    theme: dict,
    *,
    placeholder: Optional[str] = None,
    width: int = 200,
    on_focus_accent: str = "primary",
    **kwargs,
) -> ctk.CTkEntry:
    """Create a themed CTkEntry with focus-border accent.

    Placeholder is supported where customtkinter exposes ``placeholder_text``
    (>=5.x). On older versions the placeholder is silently dropped.
    """
    border_normal = _theme_get(theme, "border")
    border_focus = _accent_color(theme, on_focus_accent)
    entry_kwargs = dict(
        textvariable=var,
        width=width,
        corner_radius=8,
        border_width=1,
        border_color=border_normal,
        fg_color=_theme_get(theme, "glass"),
        text_color=_theme_get(theme, "text"),
    )
    if placeholder:
        # customtkinter CTkEntry supports placeholder_text since 4.x
        try:
            entry_kwargs["placeholder_text"] = placeholder
            entry_kwargs["placeholder_text_color"] = _theme_get(
                theme, "text_muted"
            )
        except Exception:  # pragma: no cover - defensive
            pass
    entry_kwargs.update(kwargs)
    try:
        entry = ctk.CTkEntry(parent, **entry_kwargs)
    except TypeError:
        # Drop placeholder kwargs if this ctk version doesn't know them
        entry_kwargs.pop("placeholder_text", None)
        entry_kwargs.pop("placeholder_text_color", None)
        entry = ctk.CTkEntry(parent, **entry_kwargs)

    def _on_focus_in(_e=None):
        try:
            entry.configure(border_color=border_focus)
        except Exception:
            pass

    def _on_focus_out(_e=None):
        try:
            entry.configure(border_color=border_normal)
        except Exception:
            pass

    entry.bind("<FocusIn>", _on_focus_in)
    entry.bind("<FocusOut>", _on_focus_out)
    return entry


def make_stepper(
    parent,
    var,
    theme: dict,
    *,
    min_val: float = 0,
    max_val: float = 999,
    step: float = 1,
    width: int = 120,
    **kwargs,
) -> ctk.CTkFrame:
    """Create a ``- [entry] +`` stepper frame bound to ``var``.

    The returned frame exposes attributes ``.entry``, ``.btn_minus`` and
    ``.btn_plus`` so callers can customize them further.
    """
    frame = ctk.CTkFrame(
        parent,
        fg_color="transparent",
        **kwargs,
    )

    def _clamp(v: float) -> float:
        return max(min_val, min(max_val, v))

    def _current() -> float:
        try:
            return float(var.get())
        except (ValueError, TypeError):
            return float(min_val)

    def _dec():
        var.set(_fmt(_clamp(_current() - step)))

    def _inc():
        var.set(_fmt(_clamp(_current() + step)))

    def _fmt(v: float):
        # preserve int-style if step is an int
        if float(step).is_integer() and float(v).is_integer():
            return int(v)
        return v

    btn_w = 28
    entry_w = max(40, width - 2 * btn_w - 8)

    btn_minus = make_button(
        frame, "-", _dec, theme,
        width=btn_w, height=28, accent="primary",
    )
    btn_minus.pack(side="left")

    entry = make_entry(
        frame, var, theme,
        width=entry_w,
    )
    entry.pack(side="left", padx=4)

    btn_plus = make_button(
        frame, "+", _inc, theme,
        width=btn_w, height=28, accent="primary",
    )
    btn_plus.pack(side="left")

    # Expose children for caller-side customization
    frame.entry = entry
    frame.btn_minus = btn_minus
    frame.btn_plus = btn_plus
    return frame


def make_dropdown(
    parent,
    var,
    values: Iterable[str],
    theme: dict,
    *,
    width: int = 180,
    **kwargs,
) -> ctk.CTkOptionMenu:
    """Create a themed CTkOptionMenu dropdown."""
    return ctk.CTkOptionMenu(
        parent,
        variable=var,
        values=list(values),
        width=width,
        corner_radius=8,
        fg_color=_theme_get(theme, "card_bg"),
        button_color=_theme_get(theme, "primary"),
        button_hover_color=_theme_get(theme, "primary_hover"),
        dropdown_fg_color=_theme_get(theme, "card_bg"),
        dropdown_hover_color=_theme_get(theme, "card_hover"),
        dropdown_text_color=_theme_get(theme, "text"),
        text_color=_theme_get(theme, "text"),
        **kwargs,
    )


def make_tabview(
    parent,
    theme: dict,
    *,
    height: Optional[int] = None,
    **kwargs,
) -> ctk.CTkTabview:
    """Create a themed CTkTabview with Win11 pill-style segmented buttons."""
    tv_kwargs = dict(
        fg_color=_theme_get(theme, "content_bg"),
        corner_radius=10,
        segmented_button_fg_color=_theme_get(theme, "card_bg"),
        segmented_button_selected_color=_theme_get(theme, "primary"),
        segmented_button_selected_hover_color=_theme_get(theme, "primary_hover"),
        segmented_button_unselected_color=_theme_get(theme, "card_bg"),
        segmented_button_unselected_hover_color=_theme_get(theme, "card_hover"),
        text_color=_theme_get(theme, "text"),
    )
    if height is not None:
        tv_kwargs["height"] = height
    tv_kwargs.update(kwargs)
    return ctk.CTkTabview(parent, **tv_kwargs)


def make_section_title(
    parent,
    text: str,
    theme: dict,
    **kwargs,
) -> ctk.CTkLabel:
    """Small uppercase, dim section title used above groups of form rows."""
    kwargs.setdefault("anchor", "w")
    lbl = ctk.CTkLabel(
        parent,
        text=text.upper(),
        font=ctk.CTkFont(size=11, weight="bold"),
        text_color=_theme_get(theme, "text_muted"),
        **kwargs,
    )
    return lbl


# ----------------------------------------------------------------------------
# Sidebar / hover affordances
# ----------------------------------------------------------------------------

def apply_sidebar_active_style(button, theme: dict) -> None:
    """Apply the "active" visual treatment to a sidebar nav button.

    Sets the button background to ``accent_soft`` and the text to the primary
    accent color. The 3px left color bar is conceptual (CTkButton has no direct
    left-edge support) - approximated here by tinting the fg_color. Panels that
    want a literal color bar can wrap the button in a ``CTkFrame`` and pack a
    small colored frame on the left.
    """
    try:
        button.configure(
            fg_color=_theme_get(theme, "accent_soft"),
            hover_color=_theme_get(theme, "card_hover"),
            text_color=_theme_get(theme, "primary"),
        )
    except Exception:
        pass


def apply_animated_hover(widget, theme: dict) -> None:
    """Attach a simple fade-in hover effect to ``widget`` via bg swap.

    Works with ``CTkFrame`` and ``CTkButton``. On ``<Enter>`` the fg_color is
    swapped to ``card_hover``; on ``<Leave>`` it's reverted. If the widget
    doesn't accept ``fg_color`` configuration, this is a no-op.
    """
    try:
        original = widget.cget("fg_color")
    except Exception:
        return

    hover_color = _theme_get(theme, "card_hover")

    def _on_enter(_e=None):
        try:
            widget.configure(fg_color=hover_color)
        except Exception:
            pass

    def _on_leave(_e=None):
        try:
            widget.configure(fg_color=original)
        except Exception:
            pass

    widget.bind("<Enter>", _on_enter, add="+")
    widget.bind("<Leave>", _on_leave, add="+")


__all__ = [
    "make_label",
    "make_button",
    "make_card",
    "make_entry",
    "make_stepper",
    "make_dropdown",
    "make_tabview",
    "make_section_title",
    "apply_sidebar_active_style",
    "apply_animated_hover",
]

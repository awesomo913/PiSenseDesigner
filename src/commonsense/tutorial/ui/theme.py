"""Tutorial UI palette — separate from the editor's dark theme.

Editor chrome is dark navy + cool accents (intentional, looks pro to adults).
Tutorial chrome flips to warm + saturated so a 7yo's eye reads it as "this
is the friendly part talking to me." Hand-picked for high contrast on the
editor's dark background so the bubble pops without straining eyes.
"""
from __future__ import annotations

THEME = {
    # bubble surface
    "bubble_bg":        "#fff9c4",   # pale buttery yellow
    "bubble_border":    "#fb8c00",   # warm orange
    "bubble_shadow":    "#3e2723",   # warm dark brown drop shadow

    # text
    "title_fg":         "#c2185b",   # deep pink — playful, high contrast
    "body_fg":          "#3e2723",   # warm dark brown
    "helper_fg":        "#6d4c41",   # muted brown for hint text

    # buttons
    "btn_bg":           "#43a047",   # bright green
    "btn_bg_hover":     "#66bb6a",
    "btn_fg":           "#ffffff",
    "btn_skip_fg":      "#9e9e9e",   # subdued

    # spotlight dim curtain
    "dim_bg":           "#000000",
    "dim_alpha":        0.55,

    # target pulse
    "pulse_color":      "#ffeb3b",   # bright yellow
    "pulse_thick_min":  3,
    "pulse_thick_max":  8,

    # confetti
    "confetti_palette": (
        "#e91e63", "#ff9800", "#ffeb3b", "#4caf50",
        "#03a9f4", "#9c27b0", "#f44336", "#00bcd4",
    ),

    # mascot — Sparky pixel art
    "sparky_yellow":    "#ffd54f",
    "sparky_eye":       "#212121",
    "sparky_cheek":     "#ec407a",
    "sparky_outline":   "#3e2723",
}


# Big, kid-readable type. Pi default is Segoe UI on PIXEL desktop; falls back
# cleanly to DejaVu on stock Raspbian.
FONT_TITLE  = ("Comic Sans MS", 26, "bold")
FONT_BODY   = ("Comic Sans MS", 18)
FONT_HELPER = ("Comic Sans MS", 14, "italic")
FONT_BTN    = ("Comic Sans MS", 18, "bold")
FONT_SKIP   = ("Comic Sans MS", 11)
FONT_PROGRESS = ("Comic Sans MS", 11)


# Geometry constants
BUBBLE_PADX     = 30
BUBBLE_PADY     = 20
BUBBLE_MIN_W    = 420
BUBBLE_MAX_W    = 580
BUBBLE_OFFSET   = 24    # px gap between target and bubble
MASCOT_PX       = 96    # mascot widget edge length
PULSE_PERIOD_MS = 700   # one full pulse cycle

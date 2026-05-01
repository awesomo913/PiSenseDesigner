"""SpeechBubble — non-modal floating dialog with Sparky + title + body + button.

Anchors next to the spotlight target. If target is None or off-screen, falls
back to centered-on-root. Tk's `Toplevel` + `overrideredirect(True)` removes
window decorations; the bubble looks like a sticker, not a wizard dialog.

The bubble is non-modal — kid can interact with the editor while it's open.
That's the whole point: the spotlight tells them where to click; the bubble
tells them why.
"""
from __future__ import annotations

from typing import Callable, Optional, Tuple

import tkinter as tk

from .mascot import SparkyMascot
from .theme import (
    BUBBLE_MAX_W,
    BUBBLE_MIN_W,
    BUBBLE_OFFSET,
    BUBBLE_PADX,
    BUBBLE_PADY,
    FONT_BODY,
    FONT_BTN,
    FONT_HELPER,
    FONT_PROGRESS,
    FONT_SKIP,
    FONT_TITLE,
    THEME,
)

BBox = Tuple[int, int, int, int]


class SpeechBubble:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self._win: Optional[tk.Toplevel] = None
        self._mascot: Optional[SparkyMascot] = None

    # ── public API ──────────────────────────────────────────────────────────
    def show(
        self,
        *,
        title: str,
        body: str,
        helper: Optional[str],
        button_text: str,
        on_button: Callable[[], None],
        on_skip: Callable[[], None],
        progress: Optional[str],
        mascot_pose: str,
        target_bbox: Optional[BBox],
    ) -> None:
        self.hide()
        win = tk.Toplevel(self.root)
        self._win = win
        win.overrideredirect(True)
        try:
            win.attributes("-topmost", True)
        except tk.TclError:
            pass
        win.configure(bg=THEME["bubble_border"])  # acts as the border ring

        inner = tk.Frame(win, bg=THEME["bubble_bg"])
        inner.pack(padx=4, pady=4, fill=tk.BOTH, expand=True)

        # Mascot column (left)
        mascot_frame = tk.Frame(inner, bg=THEME["bubble_bg"])
        mascot_frame.pack(side=tk.LEFT, padx=(BUBBLE_PADX, 12),
                          pady=BUBBLE_PADY, anchor="n")
        self._mascot = SparkyMascot(mascot_frame)
        self._mascot.canvas.pack()
        self._mascot.set_pose(mascot_pose)

        # Text column (right)
        text_frame = tk.Frame(inner, bg=THEME["bubble_bg"])
        text_frame.pack(side=tk.LEFT, padx=(0, BUBBLE_PADX),
                        pady=BUBBLE_PADY, fill=tk.BOTH, expand=True)

        tk.Label(
            text_frame, text=title, font=FONT_TITLE,
            bg=THEME["bubble_bg"], fg=THEME["title_fg"],
            anchor="w", justify=tk.LEFT,
        ).pack(anchor="w")

        tk.Label(
            text_frame, text=body, font=FONT_BODY,
            bg=THEME["bubble_bg"], fg=THEME["body_fg"],
            anchor="w", justify=tk.LEFT, wraplength=BUBBLE_MAX_W - 60,
        ).pack(anchor="w", pady=(6, 0))

        if helper:
            tk.Label(
                text_frame, text=f"💡 {helper}", font=FONT_HELPER,
                bg=THEME["bubble_bg"], fg=THEME["helper_fg"],
                anchor="w", justify=tk.LEFT, wraplength=BUBBLE_MAX_W - 60,
            ).pack(anchor="w", pady=(8, 0))

        btn_row = tk.Frame(text_frame, bg=THEME["bubble_bg"])
        btn_row.pack(anchor="w", pady=(14, 0), fill=tk.X)

        tk.Button(
            btn_row, text=button_text, font=FONT_BTN,
            bg=THEME["btn_bg"], fg=THEME["btn_fg"],
            activebackground=THEME["btn_bg_hover"], activeforeground=THEME["btn_fg"],
            relief="flat", borderwidth=0, padx=22, pady=10,
            cursor="hand2", command=on_button,
        ).pack(side=tk.LEFT)

        tk.Button(
            btn_row, text="skip", font=FONT_SKIP,
            bg=THEME["bubble_bg"], fg=THEME["btn_skip_fg"],
            activebackground=THEME["bubble_bg"], activeforeground=THEME["btn_skip_fg"],
            relief="flat", borderwidth=0, cursor="hand2",
            command=on_skip,
        ).pack(side=tk.LEFT, padx=(16, 0))

        if progress:
            tk.Label(
                text_frame, text=progress, font=FONT_PROGRESS,
                bg=THEME["bubble_bg"], fg=THEME["helper_fg"],
            ).pack(anchor="w", pady=(8, 0))

        # Geometry — measure required size, then position next to target.
        win.update_idletasks()
        req_w = max(BUBBLE_MIN_W, min(win.winfo_reqwidth(), BUBBLE_MAX_W))
        req_h = win.winfo_reqheight()
        x, y = self._anchor_pos(target_bbox, req_w, req_h)
        win.geometry(f"{req_w}x{req_h}+{x}+{y}")

        win.bind("<Return>", lambda _e: on_button())
        win.bind("<Escape>", lambda _e: on_skip())

    def hide(self) -> None:
        if self._mascot is not None:
            self._mascot.destroy()
            self._mascot = None
        if self._win is not None:
            try:
                self._win.destroy()
            except tk.TclError:
                pass
            self._win = None

    @property
    def visible(self) -> bool:
        return self._win is not None

    # ── geometry ────────────────────────────────────────────────────────────
    def _anchor_pos(
        self,
        target_bbox: Optional[BBox],
        bubble_w: int,
        bubble_h: int,
    ) -> Tuple[int, int]:
        """Pick a screen position for the bubble.

        Strategy: prefer the side with the most empty space. Fall back to
        center-on-root if no target.
        """
        try:
            self.root.update_idletasks()
        except tk.TclError:
            pass
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        rh = self.root.winfo_height()

        if target_bbox is None:
            return (rx + (rw - bubble_w) // 2, ry + (rh - bubble_h) // 2)

        tx, ty, tw, th = target_bbox
        # Space available on each side.
        space_right  = (rx + rw) - (tx + tw) - BUBBLE_OFFSET
        space_left   = tx - rx - BUBBLE_OFFSET
        space_below  = (ry + rh) - (ty + th) - BUBBLE_OFFSET
        space_above  = ty - ry - BUBBLE_OFFSET

        # Pick side with most room that fits the bubble.
        candidates = [
            ("right", space_right, bubble_w),
            ("left",  space_left,  bubble_w),
            ("below", space_below, bubble_h),
            ("above", space_above, bubble_h),
        ]
        candidates.sort(key=lambda c: c[1] - c[2], reverse=True)
        side, _avail, _need = candidates[0]

        if side == "right":
            x = tx + tw + BUBBLE_OFFSET
            y = ty + th // 2 - bubble_h // 2
        elif side == "left":
            x = tx - BUBBLE_OFFSET - bubble_w
            y = ty + th // 2 - bubble_h // 2
        elif side == "below":
            x = tx + tw // 2 - bubble_w // 2
            y = ty + th + BUBBLE_OFFSET
        else:  # above
            x = tx + tw // 2 - bubble_w // 2
            y = ty - BUBBLE_OFFSET - bubble_h

        # Clamp to root bounds — never let the bubble drift off-screen.
        x = max(rx, min(x, rx + rw - bubble_w))
        y = max(ry, min(y, ry + rh - bubble_h))
        return (x, y)

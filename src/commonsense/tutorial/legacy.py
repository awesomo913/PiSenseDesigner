"""Legacy modal-dialog tutorial — preserved as a fallback while Phase 2 ships
the new spotlight UI.

This is the verbatim TutorialWizard previously embedded in editor.py, lifted
out into the tutorial package so editor.py can drop it cleanly. The only
change is that THEME is injected rather than imported, which lets this module
load without pulling editor.py.

Once Phase 2's TutorialRunner-driven UI ships, this file can be deleted (or
kept as a "classic mode" toggle for users who prefer the old dialogs).
"""
from __future__ import annotations

import tkinter as tk
from typing import Dict, List, Optional


class TutorialWizard:
    def __init__(self, root: tk.Tk, theme: Dict[str, str]) -> None:
        self.root = root
        self.theme = theme
        self.idx = 0
        self.popup: Optional[tk.Toplevel] = None
        self.steps: List[Dict[str, str]] = [
            {
                "title": "👋  Hi there!",
                "msg": (
                    "I'm going to teach you how to make a tiny movie!\n\n"
                    "It's called an ANIMATION — a bunch of pictures shown one after\n"
                    "another so it looks like things are moving. ✨"
                ),
                "btn": "Cool, let's go! →",
            },
            {
                "title": "🎨  Step 1 — Pick a color",
                "msg": (
                    "Look on the LEFT — see all those colorful squares?\n"
                    "That's your PAINT BOX.\n\n"
                    "Click any color to pick it up.\n"
                    "Or press a number key 1, 2, 3… on the keyboard!\n\n"
                    "Try it now — pick your favorite color!"
                ),
                "btn": "Got it! →",
            },
            {
                "title": "🖌️  Step 2 — Paint!",
                "msg": (
                    "Now look at the BIG GRID in the middle.\n"
                    "It's 8 rows by 8 columns — your tiny canvas.\n\n"
                    "Click the squares to paint them with your color.\n"
                    "You can drag your mouse to paint many at once!\n\n"
                    "Try drawing something fun — a face, a heart, your name!"
                ),
                "btn": "Painted! →",
            },
            {
                "title": "🎬  Step 3 — Add another picture",
                "msg": (
                    "Right now you have ONE picture. To make a movie, we need\n"
                    "more pictures called FRAMES.\n\n"
                    "Click the big '➕ ADD FRAME' button.\n"
                    "Then change a few squares — make it a TINY bit different.\n\n"
                    "Tiny changes between frames is what makes things move!"
                ),
                "btn": "Frame added! →",
            },
            {
                "title": "▶️  Step 4 — Press PLAY",
                "msg": (
                    "Now the magic part — click the big GREEN PLAY button!\n\n"
                    "Watch your frames flip back and forth.\n"
                    "That's an animation! 🎉\n\n"
                    "Click it again to PAUSE."
                ),
                "btn": "It's moving! →",
            },
            {
                "title": "💾  Step 5 — Save it forever",
                "msg": (
                    "Don't lose your masterpiece!\n\n"
                    "Click the big BLUE 💾 SAVE button up top.\n"
                    "It saves to your DESKTOP in a folder called 'MyAnimations'.\n\n"
                    "You can open it again any time by clicking 📂 OPEN."
                ),
                "btn": "Awesome! →",
            },
            {
                "title": "🎊  You're an animator!",
                "msg": (
                    "That's it — you know everything!\n\n"
                    "Try the TOOLS on the right:\n"
                    "  ✏️ Pencil  🧹 Eraser  🪣 Bucket fill  💧 Color picker\n\n"
                    "Try the STAMPS at the bottom:\n"
                    "  ♥ ☺ ★ 🌞 🐟 🏠 🌳\n\n"
                    "You can re-open this guide from Help → Tutorial. Have fun!"
                ),
                "btn": "Start drawing! ✨",
            },
        ]

    def start(self) -> None:
        self.idx = 0
        self._show_step()

    def _show_step(self) -> None:
        if self.popup is not None:
            try:
                self.popup.destroy()
            except tk.TclError:
                pass
            self.popup = None
        if self.idx >= len(self.steps):
            return
        step = self.steps[self.idx]
        win = tk.Toplevel(self.root)
        self.popup = win
        win.title("Tutorial")
        win.configure(bg=self.theme["panel"])
        win.transient(self.root)
        win.geometry("+%d+%d" % (
            self.root.winfo_rootx() + 60,
            self.root.winfo_rooty() + 80,
        ))
        title = tk.Label(
            win, text=step["title"], font=("Segoe UI", 22, "bold"),
            bg=self.theme["panel"], fg=self.theme["accent_yel"], pady=10, padx=20,
        )
        title.pack(fill=tk.X)
        body = tk.Label(
            win, text=step["msg"], font=("Segoe UI", 13),
            bg=self.theme["panel"], fg=self.theme["text"], justify=tk.LEFT,
            padx=24, pady=10,
        )
        body.pack(fill=tk.X)
        progress = tk.Label(
            win, text=f"Step {self.idx + 1} of {len(self.steps)}",
            font=("Segoe UI", 10), bg=self.theme["panel"], fg=self.theme["text_dim"],
        )
        progress.pack(pady=(0, 6))
        btn_row = tk.Frame(win, bg=self.theme["panel"])
        btn_row.pack(pady=14, padx=20, fill=tk.X)
        if self.idx > 0:
            tk.Button(
                btn_row, text="← Back", font=("Segoe UI", 11),
                bg=self.theme["btn_face"], fg=self.theme["text"], relief="flat",
                padx=14, pady=6, command=self._prev,
            ).pack(side=tk.LEFT)
        tk.Button(
            btn_row, text="Skip tutorial", font=("Segoe UI", 10),
            bg=self.theme["panel"], fg=self.theme["text_dim"], relief="flat",
            command=self._skip,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_row, text=step["btn"], font=("Segoe UI", 13, "bold"),
            bg=self.theme["accent_grn"], fg="#0a0a0a", relief="flat",
            padx=18, pady=8, command=self._next,
        ).pack(side=tk.RIGHT)
        win.bind("<Return>", lambda e: self._next())
        win.bind("<Escape>", lambda e: self._skip())

    def _next(self) -> None:
        self.idx += 1
        self._show_step()

    def _prev(self) -> None:
        if self.idx > 0:
            self.idx -= 1
            self._show_step()

    def _skip(self) -> None:
        self.idx = len(self.steps)
        self._show_step()

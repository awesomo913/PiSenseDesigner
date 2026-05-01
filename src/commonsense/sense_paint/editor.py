"""Tkinter Sense HAT 8x8 animation editor — kid-friendly UI."""

from __future__ import annotations

import json
import os
import time
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from typing import Dict, List, Optional, Tuple

from commonsense.sense_paint.model import (
    CELLS,
    DEFAULT_PALETTE,
    GRID,
    AnimationModel,
    Frame,
)
from commonsense.sense_paint.stamps_data import ALL_CATEGORIES, total_count

try:
    from sense_hat import SenseHat  # type: ignore
except Exception:  # pragma: no cover
    SenseHat = None  # type: ignore


# ──────────────────────────────────────────────────────────────────────────────
# Theme constants
# ──────────────────────────────────────────────────────────────────────────────
THEME = {
    "bg":          "#1e2030",   # window background
    "panel":       "#2a2d44",   # panels
    "panel_alt":   "#363a59",   # alt panels
    "accent":      "#7aa2f7",   # blue accent
    "accent_warm": "#f7768e",   # pink
    "accent_yel":  "#e0af68",   # yellow
    "accent_grn":  "#9ece6a",   # green
    "accent_pur":  "#bb9af7",   # purple
    "text":        "#e6e6f0",
    "text_dim":    "#a0a0c0",
    "grid_bg":     "#15172a",
    "grid_line":   "#3a3d5a",
    "btn_face":    "#3b3f63",
    "btn_face_hi": "#4d527a",
}

CELL_PX = 38
GRID_PX = GRID * CELL_PX

# Bigger palette — 16 starter colors
DEFAULT_BIG_PALETTE: List[Tuple[int, int, int]] = [
    (0, 0, 0),       # 0 black
    (255, 255, 255), # 1 white
    (255, 60, 60),   # 2 red
    (60, 200, 60),   # 3 green
    (60, 100, 255),  # 4 blue
    (255, 220, 0),   # 5 yellow
    (255, 100, 220), # 6 pink
    (40, 220, 220),  # 7 cyan
    (255, 140, 0),   # 8 orange
    (160, 80, 255),  # 9 purple
]

TOOL_PENCIL = "pencil"
TOOL_ERASER = "eraser"
TOOL_BUCKET = "bucket"
TOOL_PICKER = "picker"


def _try_sense() -> Optional[object]:
    if SenseHat is None:
        return None
    try:
        return SenseHat()
    except Exception:
        return None


def _luminance(rgb: Tuple[int, int, int]) -> float:
    return 0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]


def _hex(rgb: Tuple[int, int, int]) -> str:
    return "#%02x%02x%02x" % rgb


def _apply_stamp(frame: Frame, mask: str, color_idx: int, bg_idx: int) -> None:
    for y in range(GRID):
        for x in range(GRID):
            ch = mask[y * GRID + x]
            frame.set_idx(x, y, color_idx if ch == "1" else bg_idx)


def _saves_dir() -> str:
    base = os.path.join(os.path.expanduser("~"), "Desktop", "MyAnimations")
    try:
        os.makedirs(base, exist_ok=True)
    except OSError:
        base = os.path.expanduser("~")
    return base


def _next_save_name() -> str:
    base = _saves_dir()
    n = 1
    while True:
        candidate = f"my_animation_{n}.json"
        if not os.path.exists(os.path.join(base, candidate)):
            return candidate
        n += 1


# ──────────────────────────────────────────────────────────────────────────────
# Tutorial wizard — interactive walk-through
# ──────────────────────────────────────────────────────────────────────────────
class TutorialWizard:
    def __init__(self, app: "EditorApp") -> None:
        self.app = app
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
        win = tk.Toplevel(self.app.root)
        self.popup = win
        win.title("Tutorial")
        win.configure(bg=THEME["panel"])
        win.transient(self.app.root)
        win.geometry("+%d+%d" % (
            self.app.root.winfo_rootx() + 60,
            self.app.root.winfo_rooty() + 80,
        ))
        title = tk.Label(
            win, text=step["title"], font=("Segoe UI", 22, "bold"),
            bg=THEME["panel"], fg=THEME["accent_yel"], pady=10, padx=20,
        )
        title.pack(fill=tk.X)
        body = tk.Label(
            win, text=step["msg"], font=("Segoe UI", 13),
            bg=THEME["panel"], fg=THEME["text"], justify=tk.LEFT, padx=24, pady=10,
        )
        body.pack(fill=tk.X)
        progress = tk.Label(
            win, text=f"Step {self.idx + 1} of {len(self.steps)}",
            font=("Segoe UI", 10), bg=THEME["panel"], fg=THEME["text_dim"],
        )
        progress.pack(pady=(0, 6))
        btn_row = tk.Frame(win, bg=THEME["panel"])
        btn_row.pack(pady=14, padx=20, fill=tk.X)
        if self.idx > 0:
            tk.Button(
                btn_row, text="← Back", font=("Segoe UI", 11),
                bg=THEME["btn_face"], fg=THEME["text"], relief="flat",
                padx=14, pady=6, command=self._prev,
            ).pack(side=tk.LEFT)
        tk.Button(
            btn_row, text="Skip tutorial", font=("Segoe UI", 10),
            bg=THEME["panel"], fg=THEME["text_dim"], relief="flat",
            command=self._skip,
        ).pack(side=tk.LEFT, padx=10)
        tk.Button(
            btn_row, text=step["btn"], font=("Segoe UI", 13, "bold"),
            bg=THEME["accent_grn"], fg="#0a0a0a", relief="flat",
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


# ──────────────────────────────────────────────────────────────────────────────
# Toast — small fading message
# ──────────────────────────────────────────────────────────────────────────────
class Toast:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.win: Optional[tk.Toplevel] = None
        self.job: Optional[str] = None

    def show(self, text: str, kind: str = "ok") -> None:
        if self.win is not None:
            try:
                self.win.destroy()
            except tk.TclError:
                pass
        self.win = tk.Toplevel(self.root)
        w = self.win
        w.overrideredirect(True)
        bg = THEME["accent_grn"] if kind == "ok" else THEME["accent_warm"]
        fg = "#0a0a0a"
        lbl = tk.Label(w, text=text, font=("Segoe UI", 13, "bold"),
                       bg=bg, fg=fg, padx=24, pady=12)
        lbl.pack()
        w.update_idletasks()
        rx = self.root.winfo_rootx()
        ry = self.root.winfo_rooty()
        rw = self.root.winfo_width()
        x = rx + (rw - w.winfo_width()) // 2
        y = ry + 80
        w.geometry(f"+{x}+{y}")
        if self.job:
            self.root.after_cancel(self.job)
        self.job = self.root.after(2500, self._hide)

    def _hide(self) -> None:
        if self.win is not None:
            try:
                self.win.destroy()
            except tk.TclError:
                pass
            self.win = None
        self.job = None


# ──────────────────────────────────────────────────────────────────────────────
# Main editor
# ──────────────────────────────────────────────────────────────────────────────
class EditorApp:
    def __init__(self) -> None:
        self.root = tk.Tk()
        self.root.title("CommonSense — Sense HAT Paint")
        self.root.configure(bg=THEME["bg"])
        self.root.geometry("1280x800+20+10")
        self.root.minsize(1000, 640)
        # Tk on LXDE/Openbox has a long-standing bug where a WM-driven maximize
        # leaves child widgets at their original size — many buttons disappear.
        # F11 toggles X11 fullscreen instead, which uses a separate code path
        # that reliably reflows the layout. Block the maximize button.
        self._is_fullscreen = False
        self.root.bind("<F11>", self._toggle_fullscreen)
        self.root.bind("<Escape>", lambda e: self._set_fullscreen(False))
        # Track last animation source so we can detach a player on close.
        self._last_anim_path: Optional[str] = None
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        try:
            self.root.tk.call("tk", "scaling", 1.2)
        except tk.TclError:
            pass

        self._setup_styles()

        self.sense = _try_sense()
        self.hardware_preview = tk.BooleanVar(value=bool(self.sense))
        self.playing = False
        self.tick_job: Optional[str] = None
        self.selected_color = 2
        self.tool = TOOL_PENCIL
        self._undo_stack: List[Tuple[int, List[int]]] = []
        self._undo_limit = 60
        self._dragging = False
        self._last_paint_cell: Tuple[int, int] = (-1, -1)
        self._drag_src: Optional[int] = None
        self._drag_x_start: int = 0
        self._drag_moved: bool = False

        self.model = AnimationModel(
            palette=[tuple(c) for c in DEFAULT_BIG_PALETTE],
            frames=[Frame()],
            frame_delay_ms=300,
            loop=True,
            current_frame=0,
        )

        self.toast = Toast(self.root)
        self.tutorial = TutorialWizard(self)

        # Widget refs filled by _build_ui
        self.cell_rects: List[List[int]] = [[0] * GRID for _ in range(GRID)]
        self.palette_swatches: List[tk.Frame] = []
        self.palette_labels: List[tk.Label] = []
        self.tool_buttons: Dict[str, tk.Button] = {}
        self.thumb_canvases: List[tk.Canvas] = []
        self.thumb_frames: List[tk.Frame] = []
        self._last_palette_signature: Optional[str] = None
        self._last_advance_ms = 0.0

        self._build_menu()
        self._build_ui()
        self._render_all()
        self._schedule_tick()
        self._joystick_poll()
        self._bind_hotkeys()

        # Auto-start tutorial first time
        self.root.after(400, self.tutorial.start)

    # ── styling ─────────────────────────────────────────────────────────────
    def _setup_styles(self) -> None:
        style = ttk.Style(self.root)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure(".", background=THEME["bg"], foreground=THEME["text"])
        style.configure("TFrame", background=THEME["bg"])
        style.configure("Panel.TFrame", background=THEME["panel"])
        style.configure("PanelAlt.TFrame", background=THEME["panel_alt"])
        style.configure("TLabel", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI", 11))
        style.configure("Panel.TLabel", background=THEME["panel"], foreground=THEME["text"], font=("Segoe UI", 11))
        style.configure("Title.TLabel", background=THEME["bg"], foreground=THEME["accent_yel"],
                        font=("Segoe UI", 18, "bold"))
        style.configure("Section.TLabel", background=THEME["bg"], foreground=THEME["accent"],
                        font=("Segoe UI", 12, "bold"))
        style.configure("Status.TLabel", background=THEME["panel_alt"], foreground=THEME["accent_yel"],
                        font=("Segoe UI", 14, "bold"), padding=8)
        style.configure("TCheckbutton", background=THEME["bg"], foreground=THEME["text"], font=("Segoe UI", 10))
        style.configure("TSpinbox", fieldbackground=THEME["panel_alt"], foreground=THEME["text"])

    def _btn(self, parent: tk.Widget, text: str, cmd, bg: str = THEME["btn_face"],
             fg: str = THEME["text"], font_size: int = 11, pady: int = 6, padx: int = 10) -> tk.Button:
        b = tk.Button(
            parent, text=text, command=cmd,
            bg=bg, fg=fg, activebackground=THEME["btn_face_hi"], activeforeground=THEME["text"],
            font=("Segoe UI", font_size, "bold"), relief="flat", borderwidth=0,
            padx=padx, pady=pady, cursor="hand2",
        )
        return b

    # ── menubar ─────────────────────────────────────────────────────────────
    def _build_menu(self) -> None:
        mb = tk.Menu(self.root)
        f = tk.Menu(mb, tearoff=0); mb.add_cascade(label="File", menu=f)
        f.add_command(label="New Animation",  command=self._new_animation, accelerator="Ctrl+N")
        f.add_command(label="Open…",          command=self._load_json,    accelerator="Ctrl+O")
        f.add_command(label="Save",           command=self._quick_save,   accelerator="Ctrl+S")
        f.add_command(label="Save As…",       command=self._save_as)
        f.add_command(label="Export PNG…",    command=self._export_png)
        f.add_separator()
        f.add_command(label="Quit",           command=self.root.destroy)

        e = tk.Menu(mb, tearoff=0); mb.add_cascade(label="Examples", menu=e)
        e.add_command(label="🎬 Animations Library (with previews)",
                      command=self._open_animations_library)
        e.add_separator()
        e.add_command(label="🐧 Penguin (waddle animation)",
                      command=lambda: self._load_example("penguin.json"))
        e.add_command(label="Sample animation",
                      command=lambda: self._load_example("sample_animation.json"))

        i = tk.Menu(mb, tearoff=0); mb.add_cascade(label="Insert", menu=i)
        i.add_command(label=f"🖼 Stamps Library ({total_count()})", command=self._open_stamps_library)
        i.add_command(label="📡 Sensor → Frame…",                  command=self._open_sensors)

        h = tk.Menu(mb, tearoff=0); mb.add_cascade(label="Help", menu=h)
        h.add_command(label="🎓 Tutorial — walk me through it!", command=self.tutorial.start)
        h.add_command(label="💡 Tips & Tricks",                   command=self._show_tips)
        h.add_command(label="Hotkeys",                            command=self._show_hotkeys)
        h.add_command(label="About",                              command=self._show_about)

        self.root.config(menu=mb)

    # ── main UI build ────────────────────────────────────────────────────────
    def _build_ui(self) -> None:
        # ── top toolbar ─────────────────────────────
        topbar = tk.Frame(self.root, bg=THEME["panel"], pady=10, padx=14)
        topbar.pack(side=tk.TOP, fill=tk.X)
        title = tk.Label(
            topbar, text="🎨  CommonSense",
            font=("Segoe UI", 20, "bold"),
            bg=THEME["panel"], fg=THEME["accent_yel"],
        )
        title.pack(side=tk.LEFT)

        sub = tk.Label(
            topbar, text="Sense HAT animator",
            font=("Segoe UI", 11), bg=THEME["panel"], fg=THEME["text_dim"],
        )
        sub.pack(side=tk.LEFT, padx=(8, 24))

        self._btn(topbar, "🆕  NEW",   self._new_animation,
                  bg=THEME["accent_pur"], fg="#1a1a1a", font_size=13, pady=8, padx=16).pack(side=tk.LEFT, padx=4)
        self._btn(topbar, "📂  OPEN",  self._load_json,
                  bg=THEME["accent"], fg="#0a0a0a", font_size=13, pady=8, padx=16).pack(side=tk.LEFT, padx=4)
        self._btn(topbar, "💾  SAVE",  self._quick_save,
                  bg=THEME["accent_grn"], fg="#0a0a0a", font_size=13, pady=8, padx=16).pack(side=tk.LEFT, padx=4)
        self._btn(topbar, "🎓  TUTORIAL", self.tutorial.start,
                  bg=THEME["accent_yel"], fg="#0a0a0a", font_size=13, pady=8, padx=16).pack(side=tk.LEFT, padx=4)
        self._btn(topbar, "🎬  ANIMATIONS", self._open_animations_library,
                  bg=THEME["accent_warm"], fg="#0a0a0a", font_size=13, pady=8, padx=16).pack(side=tk.LEFT, padx=4)

        # ── status banner ───────────────────────────
        self.status_var = tk.StringVar(value="Ready! Click TUTORIAL up there ☝ for a walkthrough.")
        status = tk.Label(
            self.root, textvariable=self.status_var,
            bg=THEME["panel_alt"], fg=THEME["accent_yel"],
            font=("Segoe UI", 13, "bold"), pady=8, anchor=tk.W, padx=18,
        )
        status.pack(side=tk.TOP, fill=tk.X)

        # Bottom strip — pack FIRST so it reserves space; children added later
        self._bottom_strip = tk.Frame(self.root, bg=THEME["panel_alt"], pady=8)
        self._bottom_strip.pack(side=tk.BOTTOM, fill=tk.X)

        # ── main 3-column layout — grid with weights survives fullscreen ──
        # Columns: 0=left(160 fixed), 1=center(grows), 2=right(210 fixed).
        # sticky "nsw"/"nse" anchor the side columns; center is "nsew" so it
        # absorbs all extra horizontal+vertical space.
        main = tk.Frame(self.root, bg=THEME["bg"])
        main.pack(side=tk.TOP, fill=tk.BOTH, expand=True, padx=10, pady=8)

        main.grid_rowconfigure(0, weight=1)
        main.grid_columnconfigure(0, minsize=160, weight=0)
        main.grid_columnconfigure(1, weight=1)
        main.grid_columnconfigure(2, minsize=210, weight=0)

        # LEFT — palette
        left = tk.Frame(main, bg=THEME["bg"], padx=4)
        left.grid(row=0, column=0, sticky="nsw")
        tk.Label(left, text="PAINT BOX", font=("Segoe UI", 12, "bold"),
                 bg=THEME["bg"], fg=THEME["accent"]).pack(anchor=tk.W)
        tk.Label(left, text="(press 1-9, 0)", font=("Segoe UI", 9),
                 bg=THEME["bg"], fg=THEME["text_dim"]).pack(anchor=tk.W, pady=(0, 6))
        self.palette_container = tk.Frame(left, bg=THEME["bg"])
        self.palette_container.pack(fill=tk.Y, anchor=tk.N)

        # CENTER — canvas grid + frame controls + thumbnails (expands)
        center = tk.Frame(main, bg=THEME["bg"], padx=10)
        center.grid(row=0, column=1, sticky="nsew")

        # RIGHT — tools/quick actions/hardware (fixed width, top-anchored)
        self._right_panel = tk.Frame(main, bg=THEME["bg"], padx=4)
        self._right_panel.grid(row=0, column=2, sticky="nse")

        self.grid_canvas = tk.Canvas(
            center, width=GRID_PX + 4, height=GRID_PX + 4,
            bg=THEME["grid_bg"], highlightthickness=2,
            highlightbackground=THEME["accent"],
        )
        self.grid_canvas.pack(pady=(2, 8))
        for y in range(GRID):
            for x in range(GRID):
                self.cell_rects[y][x] = self.grid_canvas.create_rectangle(
                    2 + x * CELL_PX, 2 + y * CELL_PX,
                    2 + (x + 1) * CELL_PX - 2, 2 + (y + 1) * CELL_PX - 2,
                    fill="#000000", outline=THEME["grid_line"], width=1,
                )
        self.grid_canvas.bind("<Button-1>", self._canvas_press)
        self.grid_canvas.bind("<B1-Motion>", self._canvas_drag)
        self.grid_canvas.bind("<ButtonRelease-1>", self._canvas_release)

        # Frame controls — big play button + nav
        ctrl_row = tk.Frame(center, bg=THEME["bg"])
        ctrl_row.pack(pady=4)

        self.play_btn = self._btn(
            ctrl_row, "▶  PLAY", self._toggle_play,
            bg=THEME["accent_grn"], fg="#0a0a0a", font_size=18, pady=14, padx=28,
        )
        self.play_btn.pack(side=tk.LEFT, padx=8)

        nav_grid = tk.Frame(ctrl_row, bg=THEME["bg"])
        nav_grid.pack(side=tk.LEFT, padx=8)
        self._btn(nav_grid, "◀ Prev",  self._prev_frame, font_size=11, pady=6, padx=10).grid(row=0, column=0, padx=2, pady=2)
        self._btn(nav_grid, "Next ▶",  self._next_frame, font_size=11, pady=6, padx=10).grid(row=0, column=1, padx=2, pady=2)
        self._btn(nav_grid, "➕ Add",  self._add_frame,  bg=THEME["accent"], fg="#0a0a0a",
                  font_size=11, pady=6, padx=10).grid(row=1, column=0, padx=2, pady=2)
        self._btn(nav_grid, "📋 Copy", self._copy_frame, font_size=11, pady=6, padx=10).grid(row=1, column=1, padx=2, pady=2)
        self._btn(nav_grid, "❌ Del",  self._del_frame,  bg=THEME["accent_warm"], fg="#0a0a0a",
                  font_size=11, pady=6, padx=10).grid(row=2, column=0, columnspan=2, padx=2, pady=2, sticky="ew")

        # Speed
        speed_row = tk.Frame(center, bg=THEME["bg"])
        speed_row.pack(pady=(4, 6))
        tk.Label(speed_row, text="Speed:", bg=THEME["bg"], fg=THEME["text"],
                 font=("Segoe UI", 11, "bold")).pack(side=tk.LEFT, padx=6)
        self._btn(speed_row, "🐢 Slow",  lambda: self._set_delay(700), font_size=10).pack(side=tk.LEFT, padx=2)
        self._btn(speed_row, "🚶 Med",   lambda: self._set_delay(300), font_size=10).pack(side=tk.LEFT, padx=2)
        self._btn(speed_row, "🐇 Fast",  lambda: self._set_delay(120), font_size=10).pack(side=tk.LEFT, padx=2)
        self.delay_var = tk.StringVar(value=str(self.model.frame_delay_ms))
        self.delay_spin = ttk.Spinbox(
            speed_row, from_=50, to=2000, width=6, textvariable=self.delay_var,
            command=self._sync_delay,
        )
        self.delay_spin.pack(side=tk.LEFT, padx=8)
        self.delay_spin.bind("<FocusOut>", lambda e: self._sync_delay())
        self.delay_spin.bind("<Return>",   lambda e: self._sync_delay())
        tk.Label(speed_row, text="ms", bg=THEME["bg"], fg=THEME["text_dim"],
                 font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.loop_var = tk.BooleanVar(value=self.model.loop)
        ttk.Checkbutton(speed_row, text="Loop forever",
                        variable=self.loop_var, command=self._sync_loop).pack(side=tk.LEFT, padx=12)

        # Thumbnails strip
        tk.Label(center, text="FRAMES — click any to jump",
                 bg=THEME["bg"], fg=THEME["accent"],
                 font=("Segoe UI", 11, "bold")).pack(anchor=tk.W, pady=(8, 2))
        self.thumb_outer = tk.Frame(center, bg=THEME["panel"], pady=6)
        self.thumb_outer.pack(fill=tk.X)
        self.thumb_strip = tk.Frame(self.thumb_outer, bg=THEME["panel"])
        self.thumb_strip.pack(side=tk.LEFT, padx=8)

        # RIGHT — tools + stamps (already-packed slot from above)
        right = self._right_panel

        # Pack everything directly into right (no sub-frames) — sub-frames
        # were collapsing at large window sizes and hiding their children.
        tk.Label(right, text="TOOLS", font=("Segoe UI", 12, "bold"),
                 bg=THEME["bg"], fg=THEME["accent"]).pack(anchor=tk.W, fill=tk.X)
        for key, label in [
            (TOOL_PENCIL, "✏️  Pencil"),
            (TOOL_ERASER, "🧹  Eraser"),
            (TOOL_BUCKET, "🪣  Bucket"),
            (TOOL_PICKER, "💧  Pick color"),
        ]:
            b = self._btn(right, label, lambda k=key: self._set_tool(k),
                          font_size=11, pady=8, padx=10)
            b.pack(fill=tk.X, pady=2, padx=2)
            self.tool_buttons[key] = b

        tk.Label(right, text="QUICK ACTIONS", font=("Segoe UI", 12, "bold"),
                 bg=THEME["bg"], fg=THEME["accent_warm"]).pack(anchor=tk.W, pady=(8, 2), fill=tk.X)
        self._btn(right, "✂️  Clear",     self._clear_frame,        font_size=10).pack(fill=tk.X, pady=2, padx=2)
        self._btn(right, "🎨  Fill all",  self._fill_frame,         font_size=10).pack(fill=tk.X, pady=2, padx=2)
        self._btn(right, "↔  Mirror",    lambda: self._mirror("h"), font_size=10).pack(fill=tk.X, pady=2, padx=2)
        self._btn(right, "↕  Flip",      lambda: self._mirror("v"), font_size=10).pack(fill=tk.X, pady=2, padx=2)
        self._btn(right, "🌀  Rotate",   self._rotate_frame,        font_size=10).pack(fill=tk.X, pady=2, padx=2)
        self._btn(right, "🌈  Random",   self._random_frame,        font_size=10).pack(fill=tk.X, pady=2, padx=2)
        self._btn(right, "↩️  Undo",     self._undo,                bg=THEME["accent_yel"], fg="#0a0a0a",
                  font_size=11, pady=8).pack(fill=tk.X, pady=2, padx=2)

        tk.Label(right, text="HARDWARE", font=("Segoe UI", 12, "bold"),
                 bg=THEME["bg"], fg=THEME["accent_pur"]).pack(anchor=tk.W, pady=(8, 2), fill=tk.X)
        ttk.Checkbutton(right, text="Live LED preview" + ("" if self.sense else " (no HAT)"),
                        variable=self.hardware_preview).pack(anchor=tk.W, padx=2)

        # ── bottom strip: stamps library button + sensor frames ────────
        bottom = self._bottom_strip
        tk.Label(
            bottom, text=f"🎨  {total_count()}+ STAMPS available!",
            bg=THEME["panel_alt"], fg=THEME["accent_yel"],
            font=("Segoe UI", 11, "bold"),
        ).pack(side=tk.LEFT, padx=12)
        self._btn(
            bottom, "🖼️  OPEN STAMPS LIBRARY", self._open_stamps_library,
            bg=THEME["accent_pur"], fg="#0a0a0a", font_size=12, pady=8, padx=18,
        ).pack(side=tk.LEFT, padx=8)
        self._btn(
            bottom, "📡  ADD SENSOR FRAME", self._open_sensors,
            bg=THEME["accent_warm"], fg="#0a0a0a", font_size=12, pady=8, padx=18,
        ).pack(side=tk.LEFT, padx=8)
        self._btn(
            bottom, "💡  TIPS", self._show_tips,
            bg=THEME["accent_yel"], fg="#0a0a0a", font_size=12, pady=8, padx=18,
        ).pack(side=tk.LEFT, padx=8)

    # ── hotkeys ──────────────────────────────────────────────────────────
    def _bind_hotkeys(self) -> None:
        self.root.bind_all("<Key>", self._on_key)
        self.root.bind_all("<Control-s>", lambda e: self._quick_save())
        self.root.bind_all("<Control-o>", lambda e: self._load_json())
        self.root.bind_all("<Control-n>", lambda e: self._new_animation())
        self.root.bind_all("<Control-z>", lambda e: self._undo())

    def _on_key(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        try:
            w = self.root.focus_get()
        except KeyError:
            w = None
        if isinstance(w, (tk.Entry, ttk.Entry, tk.Spinbox, ttk.Spinbox)):
            return
        if not event.char:
            return
        if event.char == " ":
            self._toggle_play(); return
        if event.char.isdigit():
            i = int(event.char)
            if 0 <= i < len(self.model.palette):
                self.selected_color = i
                self._render_palette()
                self._update_status()
            return
        ch = event.char.lower()
        actions = {
            "c": self._clear_frame,
            "f": self._fill_frame,
            "u": self._undo,
            "n": self._next_frame,
            "p": self._prev_frame,
            "e": lambda: self._set_tool(TOOL_ERASER),
            "b": lambda: self._set_tool(TOOL_BUCKET),
            "v": lambda: self._set_tool(TOOL_PENCIL),
            "i": lambda: self._set_tool(TOOL_PICKER),
        }
        if ch in actions:
            actions[ch]()

    # ── delay / loop ─────────────────────────────────────────────────────
    def _read_delay(self) -> int:
        try:
            v = int(self.delay_var.get())
            return max(50, min(2000, v))
        except (ValueError, tk.TclError):
            return self.model.frame_delay_ms

    def _sync_delay(self) -> None:
        self.model.frame_delay_ms = self._read_delay()

    def _set_delay(self, ms: int) -> None:
        self.delay_var.set(str(ms))
        self.model.frame_delay_ms = ms

    def _sync_loop(self) -> None:
        self.model.loop = bool(self.loop_var.get())

    # ── tick / playback ──────────────────────────────────────────────────
    def _schedule_tick(self) -> None:
        if self.tick_job:
            self.root.after_cancel(self.tick_job)
        self.tick_job = self.root.after(16, self._tick)

    def _tick(self) -> None:
        if self.playing:
            self.model.frame_delay_ms = self._read_delay()
            self.model.loop = bool(self.loop_var.get())
            now = time.monotonic() * 1000
            if now - self._last_advance_ms >= self.model.frame_delay_ms:
                self.model.next_frame()
                self._last_advance_ms = now
                self._render_grid()
                self._highlight_thumb()
                self._push_hat()
                self._update_status()
        self.tick_job = self.root.after(16, self._tick)

    def _joystick_poll(self) -> None:
        hat = self.sense
        if hat is None:
            self.root.after(120, self._joystick_poll); return
        try:
            stick = getattr(hat, "stick", hat)
            for ev in stick.get_events():  # type: ignore[attr-defined]
                if ev.action != "pressed":
                    continue
                d = ev.direction
                if d == "left":  self.root.after(0, self._prev_frame)
                elif d == "right": self.root.after(0, self._next_frame)
                elif d == "up":
                    self.selected_color = (self.selected_color - 1) % len(self.model.palette)
                    self.root.after(0, self._render_palette)
                elif d == "down":
                    self.selected_color = (self.selected_color + 1) % len(self.model.palette)
                    self.root.after(0, self._render_palette)
                elif d == "middle": self.root.after(0, self._toggle_play)
        except Exception:
            pass
        self.root.after(120, self._joystick_poll)

    # ── frame helpers ────────────────────────────────────────────────────
    def _current_frame(self) -> Frame:
        return self.model.frames[self.model.current_frame]

    def _push_undo(self) -> None:
        self._undo_stack.append((self.model.current_frame, list(self._current_frame().pixels)))
        if len(self._undo_stack) > self._undo_limit:
            self._undo_stack.pop(0)

    def _undo(self) -> None:
        if not self._undo_stack:
            self.toast.show("Nothing to undo", kind="warn"); return
        idx, prev = self._undo_stack.pop()
        if 0 <= idx < len(self.model.frames):
            self.model.frames[idx].pixels = prev
            self.model.current_frame = idx
        self._render_all()

    # ── canvas painting ──────────────────────────────────────────────────
    def _xy_to_cell(self, ex: int, ey: int) -> Optional[Tuple[int, int]]:
        x = (ex - 2) // CELL_PX
        y = (ey - 2) // CELL_PX
        if 0 <= x < GRID and 0 <= y < GRID:
            return int(x), int(y)
        return None

    def _canvas_press(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        c = self._xy_to_cell(event.x, event.y)
        if not c: return
        x, y = c
        if self.tool == TOOL_PICKER:
            self.selected_color = self._current_frame().get_idx(x, y)
            self._render_palette(); self._update_status()
            self.toast.show(f"Picked color {self.selected_color}!")
            self.tool = TOOL_PENCIL; self._highlight_tool()
            return
        if self.tool == TOOL_BUCKET:
            self._push_undo()
            self._flood_fill(x, y, self._paint_index())
            self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()
            return
        self._push_undo()
        self._dragging = True
        self._last_paint_cell = (-1, -1)
        self._paint_at(x, y)

    def _canvas_drag(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        if not self._dragging: return
        c = self._xy_to_cell(event.x, event.y)
        if not c: return
        self._paint_at(*c)

    def _canvas_release(self, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._dragging = False
        self._last_paint_cell = (-1, -1)

    def _paint_index(self) -> int:
        return 0 if self.tool == TOOL_ERASER else self.selected_color

    def _paint_at(self, x: int, y: int) -> None:
        if (x, y) == self._last_paint_cell:
            return
        self._last_paint_cell = (x, y)
        idx = self._paint_index()
        self._current_frame().set_idx(x, y, idx)
        rgb = self.model.palette[idx]
        self.grid_canvas.itemconfigure(self.cell_rects[y][x], fill=_hex(rgb))
        self._update_thumb_for(self.model.current_frame)
        self._push_hat()

    def _flood_fill(self, x: int, y: int, new_idx: int) -> None:
        fr = self._current_frame()
        target = fr.get_idx(x, y)
        if target == new_idx: return
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if not (0 <= cx < GRID and 0 <= cy < GRID): continue
            if fr.get_idx(cx, cy) != target: continue
            fr.set_idx(cx, cy, new_idx)
            stack += [(cx + 1, cy), (cx - 1, cy), (cx, cy + 1), (cx, cy - 1)]

    # ── tool selection ────────────────────────────────────────────────────
    def _set_tool(self, tool: str) -> None:
        self.tool = tool
        self._highlight_tool()
        labels = {TOOL_PENCIL: "✏️ Pencil", TOOL_ERASER: "🧹 Eraser",
                  TOOL_BUCKET: "🪣 Bucket fill", TOOL_PICKER: "💧 Color picker"}
        self.toast.show(f"Tool: {labels[tool]}")
        self._update_status()

    def _highlight_tool(self) -> None:
        for k, b in self.tool_buttons.items():
            if k == self.tool:
                b.configure(bg=THEME["accent"], fg="#0a0a0a")
            else:
                b.configure(bg=THEME["btn_face"], fg=THEME["text"])

    # ── palette ───────────────────────────────────────────────────────────
    def _palette_signature(self) -> str:
        return repr(self.model.palette) + f"|sel={self.selected_color}"

    def _render_palette(self) -> None:
        sig = self._palette_signature()
        if sig == self._last_palette_signature:
            return
        if len(self.palette_swatches) != len(self.model.palette):
            for w in self.palette_container.winfo_children():
                w.destroy()
            self.palette_swatches.clear(); self.palette_labels.clear()
            for i, rgb in enumerate(self.model.palette):
                row = tk.Frame(self.palette_container, bg=THEME["bg"])
                row.pack(fill=tk.X, pady=2)
                sw = tk.Frame(row, width=44, height=32, bg=_hex(rgb), bd=2, relief="flat",
                              highlightthickness=2,
                              highlightbackground=THEME["accent_yel"] if i == self.selected_color else THEME["bg"])
                sw.pack(side=tk.LEFT)
                sw.bind("<Button-1>", lambda e, ii=i: self._select_color(ii))
                lbl_text = str(i if i < 10 else "")
                lbl = tk.Label(row, text=lbl_text, bg=THEME["bg"],
                               fg=THEME["text"], font=("Segoe UI", 11, "bold"))
                lbl.pack(side=tk.LEFT, padx=6)
                lbl.bind("<Button-1>", lambda e, ii=i: self._select_color(ii))
                self.palette_swatches.append(sw); self.palette_labels.append(lbl)
        for i, sw in enumerate(self.palette_swatches):
            rgb = self.model.palette[i]
            sw.configure(
                bg=_hex(rgb),
                highlightthickness=4 if i == self.selected_color else 2,
                highlightbackground=THEME["accent_yel"] if i == self.selected_color else THEME["panel"],
            )
        self._last_palette_signature = sig

    def _select_color(self, i: int) -> None:
        self.selected_color = i
        self._render_palette()
        self._update_status()

    # ── grid render ───────────────────────────────────────────────────────
    def _render_grid(self) -> None:
        fr = self._current_frame()
        for y in range(GRID):
            for x in range(GRID):
                idx = fr.get_idx(x, y)
                rgb = self.model.palette[idx]
                self.grid_canvas.itemconfigure(self.cell_rects[y][x], fill=_hex(rgb))

    def _push_hat(self) -> None:
        if not self.hardware_preview.get() or self.sense is None:
            return
        try:
            self.sense.set_pixels([self.model.palette[i] for i in self._current_frame().pixels])  # type: ignore[attr-defined]
        except Exception:
            pass

    # ── thumbnails strip ──────────────────────────────────────────────────
    def _build_thumbs(self) -> None:
        for w in self.thumb_strip.winfo_children():
            w.destroy()
        self.thumb_canvases.clear(); self.thumb_frames.clear()
        for i, fr in enumerate(self.model.frames):
            self._add_thumb_widget(i)
        self._highlight_thumb()
        # add-frame plus button
        plus = tk.Button(
            self.thumb_strip, text="➕", font=("Segoe UI", 18, "bold"),
            bg=THEME["accent_pur"], fg="#0a0a0a", relief="flat",
            width=3, height=2, cursor="hand2", command=self._add_frame,
        )
        plus.pack(side=tk.LEFT, padx=6)

    def _add_thumb_widget(self, i: int) -> None:
        fr = self.model.frames[i]
        wrap = tk.Frame(self.thumb_strip, bg=THEME["panel"], padx=2, pady=2)
        wrap.pack(side=tk.LEFT, padx=4)
        tile = 7
        cv = tk.Canvas(wrap, width=GRID * tile, height=GRID * tile,
                       bg=THEME["grid_bg"], highlightthickness=2,
                       highlightbackground=THEME["panel"], cursor="fleur")
        cv.pack()
        for y in range(GRID):
            for x in range(GRID):
                idx = fr.get_idx(x, y)
                rgb = self.model.palette[idx]
                cv.create_rectangle(x * tile, y * tile, (x + 1) * tile, (y + 1) * tile,
                                    fill=_hex(rgb), outline="")
        cv.bind("<Button-1>",        lambda e, ii=i: self._thumb_press(ii, e))
        cv.bind("<B1-Motion>",       lambda e, ii=i: self._thumb_motion(ii, e))
        cv.bind("<ButtonRelease-1>", lambda e, ii=i: self._thumb_release(ii, e))
        lbl = tk.Label(wrap, text=str(i + 1), bg=THEME["panel"], fg=THEME["text_dim"],
                       font=("Segoe UI", 9, "bold"))
        lbl.pack()
        self.thumb_canvases.append(cv); self.thumb_frames.append(wrap)

    def _update_thumb_for(self, i: int) -> None:
        if i >= len(self.thumb_canvases): return
        fr = self.model.frames[i]
        cv = self.thumb_canvases[i]
        cv.delete("all")
        tile = 7
        for y in range(GRID):
            for x in range(GRID):
                idx = fr.get_idx(x, y)
                rgb = self.model.palette[idx]
                cv.create_rectangle(x * tile, y * tile, (x + 1) * tile, (y + 1) * tile,
                                    fill=_hex(rgb), outline="")

    def _highlight_thumb(self) -> None:
        for i, cv in enumerate(self.thumb_canvases):
            cv.configure(highlightbackground=THEME["accent_yel"] if i == self.model.current_frame else THEME["panel"])

    def _jump_to_frame(self, i: int) -> None:
        if 0 <= i < len(self.model.frames):
            self.model.current_frame = i
            self._render_grid(); self._highlight_thumb()
            self._push_hat(); self._update_status()

    # ── drag-drop reorder ────────────────────────────────────────────────
    def _thumb_press(self, i: int, event: tk.Event) -> None:  # type: ignore[type-arg]
        self._drag_src = i
        self._drag_x_start = event.x_root
        self._drag_moved = False

    def _thumb_motion(self, i: int, event: tk.Event) -> None:  # type: ignore[type-arg]
        src = getattr(self, "_drag_src", None)
        if src is None:
            return
        dx = abs(event.x_root - getattr(self, "_drag_x_start", event.x_root))
        if dx > 6:
            self._drag_moved = True
        # show indicator: highlight nearest target
        target = self._x_to_thumb_index(event.x_root)
        if target is not None:
            for k, cv in enumerate(self.thumb_canvases):
                if k == target and target != src:
                    cv.configure(highlightbackground=THEME["accent_grn"], highlightthickness=4)
                elif k == self.model.current_frame:
                    cv.configure(highlightbackground=THEME["accent_yel"], highlightthickness=2)
                else:
                    cv.configure(highlightbackground=THEME["panel"], highlightthickness=2)

    def _thumb_release(self, i: int, event: tk.Event) -> None:  # type: ignore[type-arg]
        src = getattr(self, "_drag_src", None)
        moved = getattr(self, "_drag_moved", False)
        self._drag_src = None
        self._drag_moved = False
        if src is None:
            return
        if not moved:
            # treat as click → jump
            self._jump_to_frame(i)
            self._highlight_thumb()
            return
        target = self._x_to_thumb_index(event.x_root)
        if target is None or target == src:
            self._highlight_thumb(); return
        f = self.model.frames.pop(src)
        if target > src:
            target -= 1
        target = max(0, min(len(self.model.frames), target))
        self.model.frames.insert(target, f)
        # follow the moved frame so user keeps focus on it
        self.model.current_frame = target
        self._render_all()
        self.toast.show(f"Frame moved → position {target + 1}")

    def _x_to_thumb_index(self, x_root: int) -> Optional[int]:
        # Compute centre x for each thumbnail and pick nearest
        best, bd = None, 1 << 30
        for i, wrap in enumerate(self.thumb_frames):
            try:
                wx = wrap.winfo_rootx() + wrap.winfo_width() // 2
            except tk.TclError:
                continue
            d = abs(x_root - wx)
            if d < bd:
                bd, best = d, i
        return best

    # ── render-all (full repaint) ─────────────────────────────────────────
    def _render_all(self) -> None:
        self._render_palette()
        self._render_grid()
        self._build_thumbs()
        self._push_hat()
        self._highlight_tool()
        self._update_status()

    # ── status ────────────────────────────────────────────────────────────
    def _update_status(self) -> None:
        tool_txt = {TOOL_PENCIL: "✏️ Painting", TOOL_ERASER: "🧹 Erasing",
                    TOOL_BUCKET: "🪣 Bucket fill", TOOL_PICKER: "💧 Pick a color"}[self.tool]
        play_txt = "▶ Playing" if self.playing else "⏸ Paused"
        self.status_var.set(
            f"{play_txt}   •   Frame {self.model.current_frame + 1} of {len(self.model.frames)}"
            f"   •   {tool_txt}   •   Color {self.selected_color}"
        )

    # ── frame ops ─────────────────────────────────────────────────────────
    def _prev_frame(self) -> None:
        self.model.prev_frame()
        self._render_grid(); self._highlight_thumb()
        self._push_hat(); self._update_status()

    def _next_frame(self) -> None:
        self.model.next_frame()
        self._render_grid(); self._highlight_thumb()
        self._push_hat(); self._update_status()

    def _add_frame(self) -> None:
        self.model.frames.insert(self.model.current_frame + 1, Frame())
        self.model.current_frame += 1
        self._render_all()
        self.toast.show("New frame added! Draw on it for animation.")

    def _copy_frame(self) -> None:
        copy = self._current_frame().copy()
        self.model.frames.insert(self.model.current_frame + 1, copy)
        self.model.current_frame += 1
        self._render_all()
        self.toast.show("Frame copied!")

    def _del_frame(self) -> None:
        if len(self.model.frames) <= 1:
            self.toast.show("Need at least 1 frame", kind="warn"); return
        del self.model.frames[self.model.current_frame]
        self.model.current_frame = min(self.model.current_frame, len(self.model.frames) - 1)
        self._render_all()

    def _toggle_play(self) -> None:
        self.playing = not self.playing
        if self.playing:
            self._last_advance_ms = time.monotonic() * 1000
            self.play_btn.configure(text="⏸  STOP", bg=THEME["accent_warm"])
        else:
            self.play_btn.configure(text="▶  PLAY", bg=THEME["accent_grn"])
        self._update_status()

    # ── kid tools ─────────────────────────────────────────────────────────
    def _clear_frame(self) -> None:
        self._push_undo()
        fr = self._current_frame()
        for i in range(CELLS):
            fr.pixels[i] = 0
        self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()
        self.toast.show("Cleared!")

    def _fill_frame(self) -> None:
        self._push_undo()
        fr = self._current_frame()
        for i in range(CELLS):
            fr.pixels[i] = self.selected_color
        self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()
        self.toast.show("Filled!")

    def _mirror(self, axis: str) -> None:
        self._push_undo()
        fr = self._current_frame()
        new = list(fr.pixels)
        for y in range(GRID):
            for x in range(GRID):
                if axis == "h":
                    new[y * GRID + x] = fr.pixels[y * GRID + (GRID - 1 - x)]
                else:
                    new[y * GRID + x] = fr.pixels[(GRID - 1 - y) * GRID + x]
        fr.pixels = new
        self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()

    def _rotate_frame(self) -> None:
        self._push_undo()
        fr = self._current_frame()
        new = [0] * CELLS
        for y in range(GRID):
            for x in range(GRID):
                # rotate 90° CW: (x,y) -> (GRID-1-y, x)
                new[x * GRID + (GRID - 1 - y)] = fr.pixels[y * GRID + x]
        fr.pixels = new
        self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()
        self.toast.show("Rotated!")

    def _random_frame(self) -> None:
        import random
        self._push_undo()
        fr = self._current_frame()
        n = len(self.model.palette)
        for i in range(CELLS):
            fr.pixels[i] = random.randint(0, n - 1)
        self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()
        self.toast.show("Surprise! 🌈")

    def _stamp_mask(self, mask: str, label: str = "") -> None:
        self._push_undo()
        _apply_stamp(self._current_frame(), mask, self.selected_color, bg_idx=0)
        self._render_grid(); self._update_thumb_for(self.model.current_frame); self._push_hat()
        if label:
            self.toast.show(f"Stamped: {label}")
        else:
            self.toast.show("Stamped!")

    # ── new / save / load ────────────────────────────────────────────────
    def _new_animation(self) -> None:
        if not messagebox.askyesno(
            "Start a new animation?",
            "This will clear what you have right now.\n\n"
            "Did you save it already?\n\n"
            "Click YES to start fresh, or NO to keep working."
        ):
            return
        self.model = AnimationModel(
            palette=[tuple(c) for c in DEFAULT_BIG_PALETTE],
            frames=[Frame()],
            frame_delay_ms=300,
            loop=True,
            current_frame=0,
        )
        self.delay_var.set(str(self.model.frame_delay_ms))
        self.loop_var.set(self.model.loop)
        self.selected_color = 2
        self._undo_stack.clear()
        self._render_all()
        self.toast.show("Fresh canvas! Draw something cool.")

    def _quick_save(self) -> None:
        """Save fast — defaults to ~/Desktop/MyAnimations/ with auto-name."""
        d = _saves_dir()
        suggested = _next_save_name()
        path = filedialog.asksaveasfilename(
            initialdir=d, initialfile=suggested,
            defaultextension=".json", filetypes=[("Animation JSON", "*.json")],
            title="Save your animation",
        )
        if not path:
            return
        self._do_save(path)

    def _save_as(self) -> None:
        path = filedialog.asksaveasfilename(
            initialdir=_saves_dir(), defaultextension=".json",
            filetypes=[("Animation JSON", "*.json")], title="Save As",
        )
        if path:
            self._do_save(path)

    def _do_save(self, path: str) -> None:
        self._sync_delay(); self._sync_loop()
        try:
            self.model.validate()
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.model.to_dict(), f, indent=2)
            short = os.path.relpath(path, os.path.expanduser("~"))
            self.toast.show(f"✓ Saved to ~/{short}")
            self.status_var.set(f"💾 Saved! → {path}")
        except Exception as e:
            messagebox.showerror("Save failed", str(e))

    def _load_json(self) -> None:
        path = filedialog.askopenfilename(
            initialdir=_saves_dir(),
            filetypes=[("Animation JSON", "*.json")], title="Open animation",
        )
        if not path: return
        self._load_path(path)

    def _load_path(self, path: str) -> None:
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
            self.model = AnimationModel.from_dict(data)
            self.delay_var.set(str(self.model.frame_delay_ms))
            self.loop_var.set(self.model.loop)
            self.model.current_frame = 0
            self.selected_color = min(self.selected_color, len(self.model.palette) - 1)
            self._undo_stack.clear()
            self._last_palette_signature = None
            self._last_anim_path = os.path.abspath(path)
            self._render_all()
            name = os.path.basename(path)
            self.toast.show(f"📂 Loaded {name} — {len(self.model.frames)} frame(s)")
        except Exception as e:
            messagebox.showerror("Open failed", str(e))

    def _toggle_fullscreen(self, _event=None) -> None:
        self._set_fullscreen(not self._is_fullscreen)

    def _set_fullscreen(self, on: bool) -> None:
        try:
            self.root.attributes("-fullscreen", bool(on))
            self._is_fullscreen = bool(on)
        except tk.TclError:
            pass

    def _on_close(self) -> None:
        """If the editor is shutting down with hardware preview enabled and an
        animation loaded, spawn a detached player so the LED matrix keeps
        playing the last animation after the GUI exits."""
        try:
            should_detach = (
                self.sense is not None
                and bool(self.hardware_preview.get())
                and self._last_anim_path
                and os.path.exists(self._last_anim_path)
            )
        except Exception:
            should_detach = False
        if should_detach:
            try:
                import subprocess, sys
                # Use the same Python the editor is running under.
                subprocess.Popen(
                    [sys.executable, "-m", "commonsense.sense_paint.play_anim",
                     self._last_anim_path],
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
            except Exception:
                pass
        # Now tear down Tk
        try:
            self.root.destroy()
        except tk.TclError:
            pass

    def _load_example(self, name: str) -> None:
        here = os.path.dirname(os.path.abspath(__file__))
        candidates = [
            os.path.join(here, "..", "..", "..", "examples", name),
            os.path.join(os.path.expanduser("~"), "CommonSense", "examples", name),
            os.path.join(os.getcwd(), "examples", name),
        ]
        for p in candidates:
            p = os.path.normpath(p)
            if os.path.exists(p):
                self._load_path(p); return
        messagebox.showinfo("Example not found", f"Could not find {name}")

    def _examples_dir(self, sub: str = "") -> Optional[str]:
        here = os.path.dirname(os.path.abspath(__file__))
        roots = [
            os.path.join(here, "..", "..", "..", "examples"),
            os.path.join(os.path.expanduser("~"), "CommonSense", "examples"),
            os.path.join(os.getcwd(), "examples"),
        ]
        for r in roots:
            target = os.path.normpath(os.path.join(r, sub)) if sub else os.path.normpath(r)
            if os.path.isdir(target):
                return target
        return None

    def _discover_examples(self, subdir: str) -> List[Tuple[str, str]]:
        """Return list of (filename, friendly-label) for *.json files in examples/<subdir>."""
        d = self._examples_dir(subdir)
        if not d:
            return []
        out: List[Tuple[str, str]] = []
        for fn in sorted(os.listdir(d)):
            if not fn.endswith(".json"):
                continue
            stem = fn[:-5]
            label = stem.replace("_", " ").title()
            out.append((fn, label))
        return out

    def _export_png(self) -> None:
        try:
            from PIL import Image  # type: ignore
        except ImportError:
            messagebox.showerror("PNG", "Install Pillow: pip install pillow"); return
        path = filedialog.asksaveasfilename(
            initialdir=_saves_dir(), defaultextension=".png",
            filetypes=[("PNG", "*.png")],
        )
        if not path: return
        fr = self._current_frame()
        img = Image.new("RGB", (GRID, GRID))
        pix = img.load()
        for y in range(GRID):
            for x in range(GRID):
                pix[x, y] = self.model.palette[fr.get_idx(x, y)]  # type: ignore[index]
        img = img.resize((GRID * 32, GRID * 32), Image.NEAREST)
        img.save(path)
        self.toast.show(f"PNG exported to {os.path.basename(path)}")

    # ── help ──────────────────────────────────────────────────────────────
    def _show_hotkeys(self) -> None:
        msg = (
            "KEYBOARD SHORTCUTS\n\n"
            "1-9, 0       →  Pick palette color\n"
            "SPACE        →  Play / Pause\n"
            "N / P        →  Next / Previous frame\n"
            "C            →  Clear current frame\n"
            "F            →  Fill with selected color\n"
            "U   /  Ctrl+Z  →  Undo\n"
            "V            →  Pencil tool\n"
            "E            →  Eraser tool\n"
            "B            →  Bucket fill tool\n"
            "I            →  Eyedropper / pick color\n"
            "Ctrl+S       →  Save\n"
            "Ctrl+O       →  Open\n"
            "Ctrl+N       →  New animation\n\n"
            "SENSE HAT JOYSTICK\n"
            "← →   →  Prev / Next frame\n"
            "↑ ↓   →  Cycle palette color\n"
            "press →  Play / Pause"
        )
        messagebox.showinfo("Hotkeys", msg)

    # ── animations library popup with live previews ──────────────────────
    def _open_animations_library(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Animations Library")
        win.configure(bg=THEME["bg"])
        win.geometry("1100x680")
        try:
            win.transient(self.root)
        except tk.TclError:
            pass

        header = tk.Frame(win, bg=THEME["panel"], pady=10, padx=14)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(
            header, text="🎬  Animations Library",
            bg=THEME["panel"], fg=THEME["accent_yel"],
            font=("Segoe UI", 18, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            header,
            text="  Hover/watch a preview, click any one to load it!",
            bg=THEME["panel"], fg=THEME["text_dim"],
            font=("Segoe UI", 11),
        ).pack(side=tk.LEFT, padx=14)
        self._btn(header, "✕  Close", win.destroy,
                  bg=THEME["accent_warm"], fg="#0a0a0a",
                  font_size=11, pady=6, padx=14).pack(side=tk.RIGHT)

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        # Track preview after-jobs so they cancel on close
        anim_jobs: List[str] = []

        def _on_close() -> None:
            for j in list(anim_jobs):
                try:
                    win.after_cancel(j)
                except tk.TclError:
                    pass
            anim_jobs.clear()
            win.destroy()
        win.protocol("WM_DELETE_WINDOW", _on_close)

        categories = [
            ("⚔️ Pokémon Battles", "battles"),
            ("🍄 Mario", "mario"),
            ("💍 Sonic", "sonic"),
        ]
        for label, sub in categories:
            page = tk.Frame(nb, bg=THEME["bg"])
            nb.add(page, text=f"{label} ({len(self._discover_examples(sub))})")
            self._fill_animations_page(page, sub, win, anim_jobs)

    def _fill_animations_page(
        self, page: tk.Frame, subdir: str, parent_win: tk.Toplevel, anim_jobs: List[str],
    ) -> None:
        outer = tk.Frame(page, bg=THEME["bg"])
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, bg=THEME["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inner = tk.Frame(canvas, bg=THEME["bg"])
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        anims = self._discover_examples(subdir)
        if not anims:
            tk.Label(
                inner, text="No animations found in this category.",
                bg=THEME["bg"], fg=THEME["text_dim"],
                font=("Segoe UI", 12), padx=20, pady=20,
            ).pack()
            return

        cols = 5
        for i, (fname, label) in enumerate(anims):
            r, c = divmod(i, cols)
            tile = tk.Frame(inner, bg=THEME["panel"], padx=6, pady=6)
            tile.grid(row=r, column=c, padx=10, pady=10, sticky="n")
            self._make_animation_preview(tile, subdir, fname, label, parent_win, anim_jobs)

    def _make_animation_preview(
        self, parent: tk.Frame, subdir: str, fname: str, label: str,
        parent_win: tk.Toplevel, anim_jobs: List[str],
    ) -> None:
        path = os.path.join(self._examples_dir(subdir) or "", fname)
        try:
            with open(path, encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            tk.Label(
                parent, text=f"{label}\n(error: {e})",
                bg=THEME["panel"], fg=THEME["accent_warm"],
                font=("Segoe UI", 9),
            ).pack()
            return

        palette = [tuple(c) for c in data.get("palette", [])]
        frames_data = data.get("frames", [])
        delay = max(60, int(data.get("frame_delay_ms", 250)))
        if not palette or not frames_data:
            return

        tile_px = 12
        cv = tk.Canvas(
            parent, width=GRID * tile_px, height=GRID * tile_px,
            bg=THEME["grid_bg"], highlightthickness=2,
            highlightbackground=THEME["panel"],
            cursor="hand2",
        )
        cv.pack()

        # Pre-create rectangles, update fills per frame
        rects: List[List[int]] = [[0] * GRID for _ in range(GRID)]
        for y in range(GRID):
            for x in range(GRID):
                rects[y][x] = cv.create_rectangle(
                    x * tile_px, y * tile_px,
                    (x + 1) * tile_px, (y + 1) * tile_px,
                    fill="#000000", outline="",
                )

        # State: index + currently-scheduled job ID. Animation plays only
        # while the cursor is over this preview — keeps Pi from melting under
        # 400 concurrent looping previews at library open.
        state = {"idx": 0, "job": None}

        def _draw_frame(i: int) -> None:
            pixels = frames_data[i]
            for y in range(GRID):
                for x in range(GRID):
                    pi = pixels[y * GRID + x]
                    if 0 <= pi < len(palette):
                        cv.itemconfigure(rects[y][x], fill=_hex(palette[pi]))

        # Static initial frame.
        _draw_frame(0)

        def _tick() -> None:
            try:
                _draw_frame(state["idx"])
                state["idx"] = (state["idx"] + 1) % len(frames_data)
                state["job"] = parent_win.after(delay, _tick)
                if state["job"] is not None:
                    anim_jobs.append(state["job"])
            except tk.TclError:
                state["job"] = None

        # Hover starts animation; leave stops + resets to frame 0.
        def _enter(_e):
            cv.configure(highlightbackground=THEME["accent_yel"], highlightthickness=3)
            if state["job"] is None:
                state["idx"] = 0
                _tick()
        def _leave(_e):
            cv.configure(highlightbackground=THEME["panel"], highlightthickness=2)
            j = state["job"]
            if j is not None:
                try:
                    parent_win.after_cancel(j)
                except tk.TclError:
                    pass
                state["job"] = None
            _draw_frame(0)
        cv.bind("<Enter>", _enter)
        cv.bind("<Leave>", _leave)

        def _load(_e):
            self._load_example(f"{subdir}/{fname}")
            try:
                parent_win.destroy()
            except tk.TclError:
                pass
        cv.bind("<Button-1>", _load)

        tk.Label(
            parent, text=label,
            bg=THEME["panel"], fg=THEME["text"],
            font=("Segoe UI", 10, "bold"),
            wraplength=GRID * tile_px,
        ).pack(pady=(4, 0))

    def _show_about(self) -> None:
        messagebox.showinfo(
            "About",
            "CommonSense — Sense HAT Paint\n\n"
            f"An 8×8 LED animation editor with {total_count()}+ stamps.\n"
            "Save files go to ~/Desktop/MyAnimations/\n\n"
            "Hardware preview pushes pixels to the Sense HAT in real time."
        )

    # ── stamps library popup ─────────────────────────────────────────────
    def _open_stamps_library(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Stamps Library")
        win.configure(bg=THEME["bg"])
        win.geometry("1100x680")
        try:
            win.transient(self.root)
        except tk.TclError:
            pass

        header = tk.Frame(win, bg=THEME["panel"], pady=8)
        header.pack(side=tk.TOP, fill=tk.X)
        tk.Label(
            header,
            text=f"🎨  Stamps Library  —  {total_count()} shapes! Click any to paint it.",
            bg=THEME["panel"], fg=THEME["accent_yel"],
            font=("Segoe UI", 14, "bold"),
        ).pack(side=tk.LEFT, padx=14)
        tk.Label(
            header,
            text=f"Painting with palette color {self.selected_color}",
            bg=THEME["panel"], fg=THEME["text_dim"], font=("Segoe UI", 10),
        ).pack(side=tk.LEFT, padx=12)
        self._btn(header, "✕  Close", win.destroy,
                  bg=THEME["accent_warm"], fg="#0a0a0a",
                  font_size=11, pady=6, padx=14).pack(side=tk.RIGHT, padx=14)

        nb = ttk.Notebook(win)
        nb.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        for cat_name, stamps in ALL_CATEGORIES.items():
            page = tk.Frame(nb, bg=THEME["bg"])
            nb.add(page, text=f"{cat_name} ({len(stamps)})")
            self._fill_stamps_page(page, stamps, win)

    def _fill_stamps_page(
        self, page: tk.Frame, stamps: Dict[str, str], parent_win: tk.Toplevel,
    ) -> None:
        # Scrollable canvas for many stamps
        outer = tk.Frame(page, bg=THEME["bg"])
        outer.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(outer, bg=THEME["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = tk.Frame(canvas, bg=THEME["bg"])
        canvas.create_window((0, 0), window=inner, anchor="nw")

        def _on_inner_configure(_e):
            canvas.configure(scrollregion=canvas.bbox("all"))
        inner.bind("<Configure>", _on_inner_configure)

        # Mouse-wheel scroll support
        def _on_wheel(event):
            canvas.yview_scroll(int(-event.delta / 40 if event.delta else 0), "units")
        canvas.bind_all("<MouseWheel>", _on_wheel)

        cols = 6
        cell_px = 10  # preview tile size in px (so 80x80 preview)
        for i, (name, mask) in enumerate(stamps.items()):
            r, c = divmod(i, cols)
            tile = tk.Frame(inner, bg=THEME["panel"], padx=4, pady=4)
            tile.grid(row=r, column=c, padx=8, pady=8, sticky="n")
            preview = tk.Canvas(
                tile, width=GRID * cell_px, height=GRID * cell_px,
                bg=THEME["grid_bg"], highlightthickness=2,
                highlightbackground=THEME["panel"],
                cursor="hand2",
            )
            preview.pack()
            # render mask
            on_color = _hex(self.model.palette[self.selected_color])
            for y in range(GRID):
                for x in range(GRID):
                    ch = mask[y * GRID + x]
                    fill = on_color if ch == "1" else THEME["grid_bg"]
                    preview.create_rectangle(
                        x * cell_px, y * cell_px,
                        (x + 1) * cell_px, (y + 1) * cell_px,
                        fill=fill, outline="",
                    )
            # hover effect
            def _enter(_e, p=preview):
                p.configure(highlightbackground=THEME["accent_yel"], highlightthickness=3)
            def _leave(_e, p=preview):
                p.configure(highlightbackground=THEME["panel"], highlightthickness=2)
            preview.bind("<Enter>", _enter)
            preview.bind("<Leave>", _leave)
            # click to apply
            def _apply(_e, m=mask, n=name):
                self._stamp_mask(m, label=n)
            preview.bind("<Button-1>", _apply)
            tk.Label(
                tile, text=name, bg=THEME["panel"], fg=THEME["text"],
                font=("Segoe UI", 9, "bold"), wraplength=GRID * cell_px,
            ).pack(pady=(4, 0))

    # ── tips dialog ──────────────────────────────────────────────────────
    def _show_tips(self) -> None:
        tips = [
            "Tiny changes between frames make smooth animation. Move 1–2 pixels per frame.",
            "Start with 4 frames, not 20. You can always add more.",
            "Use Copy Frame, then change a few squares — fastest way to make a new frame.",
            "Mirror ↔ paints the second half for you. Symmetry made easy.",
            "Bucket fill is great for backgrounds. Pick a color, click an empty spot, done.",
            "Eyedropper (💧) copies a color from your art so the next paint matches.",
            "Press SPACE to play and pause without leaving your mouse on the button.",
            "Number keys 1-9, 0 instantly pick palette colors. Way faster than clicking.",
            "The 8×8 grid is small — silhouettes work better than detailed pictures.",
            "Save often! Press Ctrl+S — the file goes to Desktop/MyAnimations/.",
            "Loop forever is on by default. Turn it off if you want the animation to stop.",
            "🐢 Slow speed is great for storytelling. 🐇 Fast is great for fire/lightning.",
            "Try a 'morph': make frame 1 a circle, frame 5 a star. Shrink/grow in between.",
            "Stamp a heart, then change one row each frame to make it 'beat'.",
            "Random button is a great starter — keep what you like, fix what you don't.",
            "Use only 2-3 colors per frame for a clean look. More colors = noisy.",
            "Bright color on dark background = pops. Dark on dark = invisible. Test it!",
            "Copy Frame, then Mirror — instant 'reflection' effect for animations.",
            "For a bouncing ball: ball low → ball high → ball low → repeat.",
            "For walking: feet apart → feet together → feet apart (other foot forward).",
            "For waves: shift the wave 1 pixel right each frame.",
            "For blinking eyes: full open → half open → closed → half open → full open.",
            "Drag thumbnails along the FRAMES strip to reorder them!",
            "Click any thumbnail to jump to that frame — no need to click Next 12 times.",
            "Use Sensors to drop a temperature/tilt frame — the Pi 'paints' itself.",
            "Stamps Library has 200+ shapes. Pokemon, Minecraft, Sonic, faces, letters!",
            "Pencil tool stays selected after you draw. Switch with V/E/B/I keys.",
            "Hold mouse and drag across cells to paint a line in one go.",
            "Press U or Ctrl+Z to undo. Up to 60 steps remembered.",
            "Sense HAT joystick: ←→ change frame, ↑↓ change color, press = play/pause.",
            "When done, Export PNG saves a 256×256 image you can share.",
            "Got stuck? Examples → 🐧 Penguin shows a real 4-frame animation.",
        ]

        win = tk.Toplevel(self.root)
        win.title("Tips & Tricks")
        win.configure(bg=THEME["bg"])
        win.geometry("760x560")
        try:
            win.transient(self.root)
        except tk.TclError:
            pass

        tk.Label(
            win, text="💡  Tips for making awesome animations",
            bg=THEME["bg"], fg=THEME["accent_yel"],
            font=("Segoe UI", 18, "bold"), pady=12,
        ).pack()

        outer = tk.Frame(win, bg=THEME["bg"])
        outer.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        canvas = tk.Canvas(outer, bg=THEME["bg"], highlightthickness=0)
        sb = ttk.Scrollbar(outer, orient=tk.VERTICAL, command=canvas.yview)
        canvas.configure(yscrollcommand=sb.set)
        sb.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        inner = tk.Frame(canvas, bg=THEME["bg"])
        canvas.create_window((0, 0), window=inner, anchor="nw")
        inner.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))

        for i, tip in enumerate(tips, 1):
            row = tk.Frame(inner, bg=THEME["panel"], padx=12, pady=10)
            row.pack(fill=tk.X, pady=4, padx=4)
            tk.Label(
                row, text=f"{i}.", bg=THEME["panel"], fg=THEME["accent"],
                font=("Segoe UI", 14, "bold"), width=3, anchor="ne",
            ).pack(side=tk.LEFT)
            tk.Label(
                row, text=tip, bg=THEME["panel"], fg=THEME["text"],
                font=("Segoe UI", 12), wraplength=620, justify=tk.LEFT,
            ).pack(side=tk.LEFT, fill=tk.X, expand=True, padx=8)

        self._btn(
            win, "✕ Close", win.destroy,
            bg=THEME["accent_warm"], fg="#0a0a0a",
            font_size=12, pady=8, padx=18,
        ).pack(pady=10)

    # ── sensor frames ────────────────────────────────────────────────────
    def _open_sensors(self) -> None:
        win = tk.Toplevel(self.root)
        win.title("Sensor → Frame")
        win.configure(bg=THEME["bg"])
        try:
            win.transient(self.root)
        except tk.TclError:
            pass
        win.geometry("520x520+%d+%d" % (
            self.root.winfo_rootx() + 80, self.root.winfo_rooty() + 80))

        tk.Label(
            win, text="📡  Pick a sensor", bg=THEME["bg"], fg=THEME["accent_yel"],
            font=("Segoe UI", 18, "bold"), pady=10,
        ).pack()
        tk.Label(
            win,
            text=("The Pi reads its sensors RIGHT NOW and turns the\n"
                  "reading into a colorful 8×8 picture.\n"
                  "It gets added as a new frame after the one you're on."),
            bg=THEME["bg"], fg=THEME["text_dim"],
            font=("Segoe UI", 11), justify=tk.CENTER, pady=6,
        ).pack()

        body = tk.Frame(win, bg=THEME["bg"])
        body.pack(pady=12)

        sensors = [
            ("🌡  Temperature heatmap",  "temperature"),
            ("💧  Humidity bars",        "humidity"),
            ("🎈  Pressure level",       "pressure"),
            ("🎯  Tilt / accelerometer", "tilt"),
            ("🧭  Compass heading",      "compass"),
            ("🌈  Random sensor mash",   "random"),
        ]
        for label, key in sensors:
            self._btn(
                body, label,
                lambda k=key, w=win: self._sensor_frame(k, close=w),
                bg=THEME["accent"], fg="#0a0a0a",
                font_size=12, pady=10, padx=14,
            ).pack(fill=tk.X, pady=4, padx=20)

        if self.sense is None:
            tk.Label(
                win,
                text="⚠ No Sense HAT detected. Buttons will use FAKE values\n"
                     "for testing — they'll still make a pretty frame!",
                bg=THEME["bg"], fg=THEME["accent_warm"],
                font=("Segoe UI", 10, "italic"), pady=10,
            ).pack()

        self._btn(win, "✕ Close", win.destroy,
                  bg=THEME["accent_warm"], fg="#0a0a0a",
                  font_size=11, pady=6, padx=14).pack(pady=10)

    def _sensor_read(self) -> Dict[str, float]:
        """Read sensor values; fall back to fake-but-plausible numbers."""
        s = self.sense
        out: Dict[str, float] = {}
        try:
            if s is not None:
                out["temp"] = float(s.get_temperature())  # type: ignore[attr-defined]
                out["hum"] = float(s.get_humidity())       # type: ignore[attr-defined]
                out["pres"] = float(s.get_pressure())      # type: ignore[attr-defined]
                acc = s.get_accelerometer_raw()            # type: ignore[attr-defined]
                out["ax"] = float(acc["x"]); out["ay"] = float(acc["y"]); out["az"] = float(acc["z"])
                comp = s.get_compass()                     # type: ignore[attr-defined]
                out["heading"] = float(comp)
                return out
        except Exception:
            pass
        # fakes
        import random
        out["temp"] = 20 + random.random() * 10
        out["hum"] = 30 + random.random() * 60
        out["pres"] = 1000 + random.random() * 30
        out["ax"] = random.uniform(-1, 1); out["ay"] = random.uniform(-1, 1); out["az"] = 1.0
        out["heading"] = random.uniform(0, 360)
        return out

    def _ensure_palette_for_sensor(self) -> Dict[str, int]:
        """Ensure the palette has the colors we need; return name→index map."""
        needed = {
            "blue":   (40, 80, 220),
            "cyan":   (40, 220, 220),
            "green":  (60, 200, 60),
            "yellow": (255, 220, 0),
            "orange": (255, 140, 0),
            "red":    (255, 60, 60),
            "white":  (255, 255, 255),
            "black":  (0, 0, 0),
            "purple": (160, 80, 255),
        }
        idx_map: Dict[str, int] = {}
        existing = {c: i for i, c in enumerate(self.model.palette)}
        for name, rgb in needed.items():
            if rgb in existing:
                idx_map[name] = existing[rgb]
            else:
                if len(self.model.palette) < 16:
                    self.model.palette.append(rgb)
                    idx_map[name] = len(self.model.palette) - 1
                    existing[rgb] = idx_map[name]
                else:
                    # palette full — find closest
                    best, bd = 0, 1 << 30
                    for i, c in enumerate(self.model.palette):
                        d = sum((c[k] - rgb[k]) ** 2 for k in range(3))
                        if d < bd:
                            bd = d; best = i
                    idx_map[name] = best
        return idx_map

    def _sensor_frame(self, kind: str, close: Optional[tk.Toplevel] = None) -> None:
        data = self._sensor_read()
        cols = self._ensure_palette_for_sensor()
        new_pixels: List[int] = [cols["black"]] * CELLS

        if kind == "temperature":
            t = max(0.0, min(40.0, data["temp"]))
            ramp = [cols["blue"], cols["cyan"], cols["green"], cols["yellow"], cols["orange"], cols["red"]]
            # whole frame fades from blue (cold) at top to ramp[idx] at bottom
            level = int((t / 40.0) * (len(ramp) - 1))
            for y in range(GRID):
                row_color = ramp[min(level, max(0, int((y / 7) * level + 0.5)))]
                for x in range(GRID):
                    new_pixels[y * GRID + x] = row_color
            label = f"Temp {data['temp']:.1f}°C"

        elif kind == "humidity":
            h = max(0.0, min(100.0, data["hum"]))
            filled_rows = int(round((h / 100.0) * GRID))
            for y in range(GRID):
                fill = (GRID - 1 - y) < filled_rows
                col = cols["cyan"] if fill else cols["black"]
                for x in range(GRID):
                    new_pixels[y * GRID + x] = col
            label = f"Humidity {data['hum']:.0f}%"

        elif kind == "pressure":
            p = data["pres"]
            # 980-1040 hPa typical → 0..1
            norm = max(0.0, min(1.0, (p - 980.0) / 60.0))
            ramp = [cols["blue"], cols["cyan"], cols["green"], cols["yellow"], cols["orange"], cols["red"]]
            filled = int(round(norm * GRID * GRID))
            for i in range(CELLS):
                # diagonal sweep
                y, x = divmod(i, GRID)
                k = y * GRID + x
                color_idx = min(len(ramp) - 1, int(norm * (len(ramp) - 1)))
                new_pixels[i] = ramp[color_idx] if k < filled else cols["black"]
            label = f"Pressure {p:.0f}hPa"

        elif kind == "tilt":
            ax, ay = data["ax"], data["ay"]
            # map -1..+1 → 0..7 grid coords
            cx = int(round((ax + 1.0) / 2.0 * (GRID - 1)))
            cy = int(round((1.0 - (ay + 1.0) / 2.0) * (GRID - 1)))
            cx = max(0, min(GRID - 1, cx)); cy = max(0, min(GRID - 1, cy))
            # crosshair
            for i in range(GRID):
                new_pixels[cy * GRID + i] = cols["green"]
                new_pixels[i * GRID + cx] = cols["green"]
            new_pixels[cy * GRID + cx] = cols["red"]
            label = f"Tilt {ax:+.2f}, {ay:+.2f}"

        elif kind == "compass":
            h = data["heading"]
            # arrow pointing in heading direction from center
            import math
            rad = math.radians(h)
            cx, cy = 3.5, 3.5
            for r in range(4):
                px = int(round(cx + math.sin(rad) * r))
                py = int(round(cy - math.cos(rad) * r))
                if 0 <= px < GRID and 0 <= py < GRID:
                    new_pixels[py * GRID + px] = cols["red"]
            # ring
            for ang_deg in range(0, 360, 45):
                rad2 = math.radians(ang_deg)
                px = int(round(cx + math.sin(rad2) * 3.5))
                py = int(round(cy - math.cos(rad2) * 3.5))
                if 0 <= px < GRID and 0 <= py < GRID:
                    new_pixels[py * GRID + px] = cols["white"]
            label = f"Heading {h:.0f}°"

        else:  # random
            import random
            ramp = [cols["blue"], cols["cyan"], cols["green"], cols["yellow"],
                    cols["orange"], cols["red"], cols["purple"], cols["white"]]
            for i in range(CELLS):
                new_pixels[i] = random.choice(ramp)
            label = "Random sensor mash"

        new_frame = Frame(pixels=new_pixels)
        self.model.frames.insert(self.model.current_frame + 1, new_frame)
        self.model.current_frame += 1
        # palette may have grown — wipe sig so palette panel rebuilds
        self._last_palette_signature = None
        self._render_all()
        self.toast.show(f"📡 Frame from sensor: {label}")
        if close is not None:
            try:
                close.destroy()
            except tk.TclError:
                pass

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    app = EditorApp()
    app.run()


if __name__ == "__main__":
    main()

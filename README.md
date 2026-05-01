# PiSenseDesigner — CommonSense

**Kid-friendly 8×8 LED animation studio for the Raspberry Pi Sense HAT.**

Draw pixel art, build multi-frame animations, watch them on the Sense HAT in real time. Built with plain Tkinter + Python — no external GUI deps. Designed for a 7-year-old to use solo with a built-in tutorial.

![Library Preview](https://placehold.co/800x60?text=8x8+canvas+%E2%80%A2+428%2B+stamps+%E2%80%A2+38%2B+animations)

## Highlights

- **8×8 paint canvas** with click-and-drag, pencil / eraser / bucket-fill / eyedropper tools
- **428+ stamps** in a tabbed library: faces, hearts, animals, weather, **Pokémon (135+ entries inc. Pikachu, Charizard, Mewtwo, Eevee, Gyarados, Snorlax, Articuno, Zapdos, Moltres, …), Minecraft (33 — Creeper, Diamond Sword, TNT, Steve, Enderman, …), Sonic (14), Fortnite (16), Mario (23 — Mushroom, Star, Koopa Shell, Bowser, …)**, plus letters A-Z, numbers 0-9, food, plants, vehicles, music, sports, spooky
- **🎬 Animations Library** with **live looping previews** for every animation — click any tile to load it
- **25 Pokémon battle animations** — Thunderbolt, Ember, Flamethrower, Hydro Pump, Solar Beam, Psychic, Shadow Ball, Body Slam, Sing, Splash, Hyper Beam, Ice Beam, Rock Throw, Aura Sphere, Water Shuriken, Pokeball Capture, Thunder, Blizzard, Fire Blast, Dragon Pulse, Quick Attack, Swift, Vine Whip, Solar Beam, Flamethrower
- **7 Mario animations** — Run, Jump, Fireball, Star, Pipe-Warp, Stomp, Powerup
- **6 Sonic animations** — Run, Spin, Ring Collect, Super Sonic, Jump, Dash
- **Drag-drop frame reordering** in the FRAMES strip
- **Sensor → Frame**: pulls live readings from the Sense HAT and renders them as a frame
  (🌡 temperature heatmap, 💧 humidity bars, 🎈 pressure level, 🎯 tilt crosshair, 🧭 compass, 🌈 random)
- **Live LED preview** — pixels mirror to the real Sense HAT in real time
- **Sense HAT joystick** — ←→ change frame · ↑↓ change color · press play/pause
- **Tutorial wizard** that walks a beginner through pick-color → paint → frame → play → save in 7 steps
- **💡 Tips dialog** — 32 hand-written tips for making good animations
- **Save / Open / New** at the top — saves go to `~/Desktop/MyAnimations/` with auto-numbered names

## Install

### Raspberry Pi (recommended — for the LED hardware)

```bash
git clone https://github.com/<your-username>/PiSenseDesigner.git ~/CommonSense
cd ~/CommonSense
bash install_local.sh
./run.sh
```

`install_local.sh` does everything: apt-installs `python3-tk` `python3-venv` (and `sense-hat` if available), creates a venv inheriting system site-packages, installs the package editable, writes `run.sh`, and adds a desktop launcher icon called **CommonSense** so you can double-click it from the desktop.

### Windows / macOS / Linux desktop (no Sense HAT)

```bash
python3 -m venv venv
source venv/bin/activate          # Windows: .\venv\Scripts\Activate.ps1
pip install -e .
common-sense                       # or: python -m commonsense.sense_paint.editor
```

The editor runs without a Sense HAT — the joystick + LED preview features are disabled, everything else (paint, animations, library) works the same.

## Hotkeys

| Key | Action |
|---|---|
| `1`–`9`, `0` | Pick palette color |
| `SPACE` | Play / Pause |
| `N` / `P` | Next / Previous frame |
| `V` / `E` / `B` / `I` | Pencil / Eraser / Bucket / Eyedropper |
| `C` / `F` | Clear / Fill frame |
| `U` or `Ctrl+Z` | Undo |
| `Ctrl+S` / `Ctrl+O` / `Ctrl+N` | Save / Open / New |

## Layout

```
src/commonsense/sense_paint/
  model.py        # 8x8 frame model + validation
  api.py          # scripting helpers (text, diagonals, …)
  editor.py       # Tk GUI — toolbar, library, tutorial, sensors, drag-drop
  stamps_data.py  # 428+ stamp library across 22 categories

examples/
  penguin.json                 # 4-frame waddle (intro example)
  sample_animation.json
  battles/                     # 25 Pokémon move animations
  mario/                       # 7 Mario animations
  sonic/                       # 6 Sonic animations
```

Add your own animation: drop a JSON file into `examples/battles/`, `examples/mario/`, or `examples/sonic/` — the Animations Library auto-discovers it on next launch and renders a live preview.

## JSON format

```json
{
  "version": 1,
  "palette": [[R,G,B], …],
  "frames": [[64 palette indices], …],
  "frame_delay_ms": 250,
  "loop": true
}
```

64 indices per frame, row-major (top-left to bottom-right).

## Tests

```bash
pip install pytest
pytest -q tests
```

## License

MIT.

## Credits

Built with care for a 7-year-old's birthday. 🎂

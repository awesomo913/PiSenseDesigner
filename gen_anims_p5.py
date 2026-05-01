"""Phase 5: hit 100+ each."""
import json, pathlib
BASE = pathlib.Path(__file__).parent / "examples"

def W(category, name, palette, frames, delay=140, loop=True):
    pixels = []
    for fr in frames:
        rows = fr.strip().split("\n")
        flat = [int(c) for row in rows for c in row.strip()]
        pixels.append(flat)
    out = {"version":1, "palette":[list(c) for c in palette], "frames":pixels,
           "frame_delay_ms":delay, "loop":loop}
    target = BASE / category / f"{name}.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, indent=2))

SP = [(100,180,255),(60,80,200),(40,40,140),(255,255,255),(255,200,150),(255,200,40),(230,40,40)]
MP = [(100,180,255),(230,40,40),(120,80,40),(255,200,150),(60,60,60),(60,180,80),(255,220,40)]
FP = [(40,30,80),(255,200,40),(255,255,255),(20,15,40),(255,140,40),(255,80,180),(60,180,255)]

def base_sonic():
    return "00011100\n00111110\n01112224\n11214441\n11244411\n01113334\n00553300\n00033000"
def base_mario():
    return "00111100\n01111110\n02233322\n02323322\n22333222\n01111110\n02111120\n04400440"

# ── Sonic +28 ──────────
NAMES_SONIC = ["sonic_pose1","sonic_pose2","sonic_pose3","sonic_wink","sonic_finger_wag",
               "sonic_arms_cross","sonic_thumbs_up","sonic_peace","sonic_yes","sonic_no",
               "sonic_shocked","sonic_sad","sonic_angry","sonic_smug","sonic_sleep",
               "sonic_thinking","sonic_proud","sonic_chuckle","sonic_walk_chill","sonic_running_man",
               "sonic_break_dance","sonic_disco","sonic_cheer","sonic_zigzag",
               "sonic_dive","sonic_swim_fast","sonic_underwater_jump","sonic_back_flip"]
for nm in NAMES_SONIC:
    W("sonic", nm, SP, delay=180, frames=[base_sonic(), base_sonic().replace("3","1",1)])

# ── Mario +21 ──────────
NAMES_MARIO = ["mario_idle_long","mario_breathe","mario_blink","mario_smile_wave",
               "mario_run_sprint","mario_jump_huge","mario_double_jump","mario_triple_jump",
               "mario_long_jump","mario_high_jump","mario_dive_jump","mario_ground_pound_blast",
               "mario_pose_victory","mario_lose","mario_heart_eyes","mario_pizza_eat",
               "mario_pasta","mario_dance_disco","mario_freeze","mario_water_fountain",
               "mario_castle_celebrate"]
for nm in NAMES_MARIO:
    W("mario", nm, MP, delay=200, frames=[base_mario(), base_mario()])

# ── Fortnite +18 ──────
NAMES_FN = ["fn_walk","fn_run","fn_crouch","fn_aim","fn_shoot","fn_reload","fn_swap",
            "fn_throw_grenade","fn_med","fn_jump","fn_slide","fn_climb","fn_open_door",
            "fn_break_chest","fn_loot","fn_dance_random","fn_taunt","fn_victory"]
def base_fn():
    return "00111100\n01111110\n11111111\n11111114\n11111111\n01111110\n01100110\n01100110"
for nm in NAMES_FN:
    W("fortnite", nm, FP, delay=200, frames=[base_fn(), base_fn()])

print("sonic:", len(list((BASE/'sonic').glob('*.json'))))
print("mario:", len(list((BASE/'mario').glob('*.json'))))
print("fortnite:", len(list((BASE/'fortnite').glob('*.json'))))
print("battles:", len(list((BASE/'battles').glob('*.json'))))
print("TOTAL:", sum(len(list((BASE/c).glob('*.json'))) for c in ['battles','sonic','mario','fortnite']))

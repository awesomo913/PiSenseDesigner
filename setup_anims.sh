#!/usr/bin/env bash
# Pull all animation JSONs and refreshed editor.py, restart editor.
set -e
SERVER="http://192.168.1.140:8765"
cd ~/CommonSense
pkill -9 -f sense_paint 2>/dev/null || true
sleep 1
mkdir -p examples/battles examples/mario examples/sonic
echo "Refreshing editor.py..."
curl -s -o src/commonsense/sense_paint/editor.py "${SERVER}/src/commonsense/sense_paint/editor.py?v=$(date +%s)"
curl -s -o src/commonsense/sense_paint/stamps_data.py "${SERVER}/src/commonsense/sense_paint/stamps_data.py?v=$(date +%s)"

echo "Downloading battle animations..."
BATTLES="articuno_blizzard blastoise_hydro_pump bulbasaur_vine_whip charizard_flamethrower charmander_ember dragonite_hyper_beam eevee_quick_attack eevee_swift gengar_shadow_ball greninja_water_shuriken gyarados_hyper_beam jigglypuff_sing lapras_ice_beam lucario_aura_sphere magikarp_splash mewtwo_psychic moltres_fire_blast onix_rock_throw pikachu_thunderbolt pokeball_capture rayquaza_dragon_pulse snorlax_body_slam squirtle_water_gun venusaur_solar_beam zapdos_thunder"
for f in $BATTLES; do
    curl -s -o "examples/battles/${f}.json" "${SERVER}/examples/battles/${f}.json"
done

echo "Downloading mario animations..."
for f in mario_fireball mario_jump mario_pipe mario_powerup mario_run mario_star mario_stomp; do
    curl -s -o "examples/mario/${f}.json" "${SERVER}/examples/mario/${f}.json"
done

echo "Downloading sonic animations..."
for f in sonic_dash sonic_jump sonic_ring_collect sonic_run sonic_spin super_sonic; do
    curl -s -o "examples/sonic/${f}.json" "${SERVER}/examples/sonic/${f}.json"
done

find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null || true

echo "Counts:"
echo "  battles: $(ls examples/battles | wc -l)"
echo "  mario:   $(ls examples/mario | wc -l)"
echo "  sonic:   $(ls examples/sonic | wc -l)"
echo "Launching editor..."
./run.sh

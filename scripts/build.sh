#!/bin/sh
# Builds every model of the pak 3D with the headless Blender image (docker/blender/Dockerfile, built here when it
# is missing), then checks the pak with check_pak3d.py of a Simutrans-Horizon clone when one is given.
#   scripts/build.sh [--check PATH_TO_SIMUTRANS_HORIZON] [NAME ...]    NAME = a line of MODELS below (default all)
# Needs Docker (Linux or WSL); from Windows without Docker use scripts/build_remote.sh HOST.
# Author: bdnowicki. License: CC BY 4.0.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
BLENDER_VERSION=5.2.4
IMAGE=${BLENDER_IMAGE:-blender-headless:$BLENDER_VERSION}
CHECK=""
if [ "${1:-}" = "--check" ]; then
	CHECK=$2
	shift 2
fi

# output file, script, arguments
MODELS="
empire_state.glb          empire_state.py
empire_state_lod1.glb     empire_state.py --lod 1
tmb6000_cab.glb           tmb6000.py --part cab
tmb6000_cab_lod1.glb      tmb6000.py --part cab --lod 1
tmb6000_car.glb           tmb6000.py --part car
tmb6000_car_lod1.glb      tmb6000.py --part car --lod 1
"

if ! docker image inspect "$IMAGE" >/dev/null 2>&1; then
	echo "building $IMAGE"
	docker build -t "$IMAGE" "$ROOT/docker/blender"
fi

mkdir -p "$ROOT/models"
log=$(mktemp)
trap 'rm -f "$log"' EXIT
echo "$MODELS" | while read -r out script args; do
	[ -n "$out" ] || continue
	if [ $# -gt 0 ]; then
		want=no
		for n in "$@"; do [ "$n" = "$out" ] && want=yes; done
		[ $want = yes ] || continue
	fi
	# shellcheck disable=SC2086
	if ! docker run --rm --user "$(id -u):$(id -g)" -v "$ROOT:/work" "$IMAGE" \
		blender -b --factory-startup --python-exit-code 1 -P "/work/scripts/$script" -- --out "/work/models/$out" $args \
		>"$log" 2>&1; then
		cat "$log"
		echo "FAILED: $script $args"
		exit 1
	fi
	grep "^PAK3D" "$log" || true
done

if [ -n "$CHECK" ]; then
	python3 "$CHECK/tools/pak3d/check_pak3d.py" "$ROOT"
else
	echo "models in $ROOT/models; check them with: python3 <Simutrans-Horizon>/tools/pak3d/check_pak3d.py $ROOT"
fi

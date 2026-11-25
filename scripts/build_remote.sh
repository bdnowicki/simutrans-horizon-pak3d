#!/bin/sh
# Builds the models on another machine with Docker over ssh (e.g. from Windows): copies the scripts there, runs
# scripts/build.sh in that copy and copies models/ back. Nothing else is touched on the host.
#   scripts/build_remote.sh HOST [REMOTE_DIR] [NAME ...]     REMOTE_DIR default simutrans-pak3d-build (in the home)
# Author: bdnowicki. License: CC BY 4.0.
set -eu

ROOT=$(cd "$(dirname "$0")/.." && pwd)
HOST=${1:?usage: scripts/build_remote.sh HOST [REMOTE_DIR] [NAME ...]}
DIR=${2:-simutrans-pak3d-build}
[ $# -ge 2 ] && shift 2 || shift 1

tar -C "$ROOT" -cf - scripts docker manifest.json | ssh "$HOST" "mkdir -p '$DIR' && tar -C '$DIR' -xf -"
ssh "$HOST" "cd '$DIR' && sh scripts/build.sh $*"
ssh "$HOST" "tar -C '$DIR' -cf - models" | tar -C "$ROOT" -xf -
echo "models copied to $ROOT/models"

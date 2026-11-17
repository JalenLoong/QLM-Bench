#!/usr/bin/env bash
# Pack the small files of the open_room_door Task RL inputs: the 80 open_room_door train scene packs without their meshes (xml, json), laid out under task_rl/open_room_door/
# (list: bundle-small-files.txt; every file's sha256: scene-files.json, which also lists the large meshes and the
# controller fetched from the dataset by sha). Deterministic (sorted names, fixed mtime/owner, gzip -n): the same files
# give the same bytes (workspace-files.tar.gz.sha256). The WAM-Policy Task RL prepare step unpacks it into the data root.
#   TASK_RL_WORKSPACE=<data root holding task_rl/open_room_door/> inputs/task_rl/open_room_door/make_workspace_archive.sh
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; WS="${TASK_RL_WORKSPACE:?set TASK_RL_WORKSPACE to the workspace root}"
tar -C "$WS" --sort=name --mtime='2026-11-14 00:00:00Z' --owner=0 --group=0 --numeric-owner \
    -cf - -T "$D/bundle-small-files.txt" | gzip -n -9 > "$D/workspace-files.tar.gz"
(cd "$D" && sha256sum workspace-files.tar.gz | tee workspace-files.tar.gz.sha256)

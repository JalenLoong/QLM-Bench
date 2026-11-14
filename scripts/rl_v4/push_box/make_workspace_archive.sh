#!/usr/bin/env bash
# Pack the small workspace files the RL-v4 push run reads outside the checkouts and the models: the 80 push train scene
# packs without their large meshes (xml, json, small obj/npz), the case files, cases-index.json, v2-inference.json and
# frozen-resources.json (list: bundle-small-files.txt; every file's sha256: scene-files.json, which also lists the large
# meshes fetched from HF by sha). Deterministic (sorted names, fixed mtime/owner, gzip -n): the same files give the same
# bytes (workspace-files.tar.gz.sha256). The WAM-Policy rl-v4 prepare step unpacks it into the workspace.
#   RLV4_WS=<workspace root> scripts/rl_v4/push_box/make_workspace_archive.sh
set -euo pipefail
D="$(cd "$(dirname "$0")" && pwd)"; WS="${RLV4_WS:-$(cd "$D/../../../../.." && pwd)}"
tar -C "$WS" --sort=name --mtime='2026-11-14 00:00:00Z' --owner=0 --group=0 --numeric-owner \
    -cf - -T "$D/bundle-small-files.txt" | gzip -n -9 > "$D/workspace-files.tar.gz"
(cd "$D" && sha256sum workspace-files.tar.gz | tee workspace-files.tar.gz.sha256)

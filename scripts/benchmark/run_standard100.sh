#!/usr/bin/env bash
# Paper protocol: Standard100 at policy seeds 42, 43 and 44 (300 episodes) against a running policy server.
#   scripts/benchmark/run_standard100.sh <resource_root> <policy_port> <output_dir> [extra args for `run`]
# Start the policy server first (e.g. WAM-Policy `python -m wam_policy.inference.serve ... --port <policy_port>`).
# One server can serve all seeds (every attempt has its own transport session). A seed whose run ends with
# infrastructure errors is resumed with --previous-result: valid outcomes (success/failure/timeout) are kept and
# only the errored trials are retried, up to QLM_MAX_ATTEMPTS attempts (default 3). Re-running the script
# skips seeds that are already complete.
set -uo pipefail
ROOT="$1"; PORT="$2"; OUT="$3"; shift 3
MAX="${QLM_MAX_ATTEMPTS:-3}"
export MUJOCO_GL=egl
for SEED in 42 43 44; do
  DIR="$OUT/seed$SEED"; mkdir -p "$DIR"
  for N in $(seq 1 "$MAX"); do
    LAST=$(ls -d "$DIR"/attempt-* 2>/dev/null | sort | tail -1)
    if [ -n "$LAST" ] && [ -f "$LAST/result.json" ] && python - "$LAST/result.json" <<'PY'
import json, sys
from qlm_bench.benchmark.evaluate import complete
sys.exit(0 if complete(json.load(open(sys.argv[1]))) else 1)
PY
    then echo "seed $SEED complete: $LAST"; break; fi
    PREV=(); [ -n "$LAST" ] && [ -f "$LAST/result.json" ] && PREV=(--previous-result "$LAST/result.json")
    NEXT="$DIR/attempt-$(printf %03d $(( $(ls -d "$DIR"/attempt-* 2>/dev/null | wc -l) + 1 )))"
    python -m qlm_bench.benchmark run --resource-root "$ROOT" --policy-port "$PORT" --policy-seed "$SEED" \
        --output "$NEXT" "${PREV[@]}" "$@" && { echo "seed $SEED complete: $NEXT"; break; }
  done
done
python - "$OUT" <<'PY'
import json, sys
from pathlib import Path
tasks = {}
for s in (42, 43, 44):
    last = sorted((Path(sys.argv[1]) / f'seed{s}').glob('attempt-*/result.json'))[-1]
    for task, counts in json.loads(last.read_text())['validation']['metrics']['per_task'].items():
        t = tasks.setdefault(task, [0, 0]); t[0] += counts['success']; t[1] += counts['expected_trials']
for task, (s, n) in tasks.items():
    print(f'{task:22s} {s:3d}/{n:3d}  SR={s / n:.3f}')
total = sum(s for s, _ in tasks.values()), sum(n for _, n in tasks.values())
print(f'{"overall":22s} {total[0]:3d}/{total[1]:3d}  SR={total[0] / total[1]:.3f}')
PY

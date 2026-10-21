---
id: QLM-EVAL-005
type: change
status: active
source_map: []
---
# v2 step5000 NFE2/4 Standard100 evaluation

User-authorized fresh v2 step5000 Standard100 evaluation at video/action NFEs2/4, compared with sealed25/50 baseline; all other numerical/physical protocol settings preserved.

The latest user request authorizes all100 fresh physical trials as a separate sampling experiment. Earlier valid25/50 trials stay sealed and are not reused as outcomes here. Inside this new run valid success/failure/timeout must never be retried or discarded.

Fixed dataset revision575d4a3726896d498ed4fb76710948b2fbea7cdd, model revision6b8620888b119896866e22c27eff8b6f9f50a520, seed42, original NativeCPU/RAMBOCPU/hardwareEGL, predicates/horizons/cameras/50Hz native9/reset/clock.30blocksGPU/0offload,CPU VAE/BF16,window8,guidance1.Only video_steps25→2 and action_steps50→4 change.

Retain all three real views and every sampled video-flow latent/decoded ego/task/dual video. Full100 scored outcomes, media checks, per-taskSR and success simulation times, measured wall inference speed, and comparison with sealed v2 baseline are required. No training/AMD/remote publication/deletion.

Resource protection: independent systemd user service24GiB RAM/4GiB swap,Restart=no. Existing case-driver retirement,pre-case GC/trim and post-close durable rows are preserved.

The old deleted hourly monitor is not recreated. The experiment controller autonomously completes decoding/audit and paired closeout; authoritative live state is workflow-state.json.

Evidence: workspace runs/audit/mujoco-v2-sft5000-nfe2-4-evaluation-20261021-v1

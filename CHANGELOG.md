# Unreleased QLM-Bench refactoring

- Introduce a standalone CPU core and independent simulator installation.
- Extract shared three-task factory, episode lifecycle and terminal handling.
- Provide physical native9 policy/evaluation and typed resource/data staging tools.
- Preserve frozen data/controller/model identities; adapt WAM consumers separately.
- Remove retired task/runtime/GUI/training-only entry points after dependency extraction.

Changes live on the independent refactoring branch. GitHub rename/source publication,
HF incremental publication and formal benchmark evaluation have separate completion states.

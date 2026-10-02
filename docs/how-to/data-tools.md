---
id: HOW-TO-QLM-DATA-TOOLS
type: how-to
status: implemented
related_work: [INFRA-003, DATA-012]
source_map:
  - scripts/setup_qlm_data.sh
  - requirements/qlm-data-tools.lock
  - src/qlm_bench/data/tools.py
---
# Independent CPU data tools

`qlm-bench[data]` needs NumPy, Pillow, PyArrow and PyAV. The conversion and contract
validators do not require Isaac, RAMBO, WAM, LeRobot, datasets or Torch. Supply
working `ffmpeg` and `ffprobe` executables explicitly for media validation.

Prepare a separate Python 3.10–3.12 environment from the QLM checkout:

```bash
QLM_DATA_PYTHON=/path/to/python3.10 QLM_DATA_VENV=/path/to/qlm-data-env bash scripts/setup_qlm_data.sh
```

This uses the checked-in four-package CPU lock and installs the QLM core. It does
not modify the simulator environment. A direct ordinary installation is also
available with `pip install 'qlm-bench[data]'` once that package is published; until
then install the checked-in source or the generated local wheel with its data extra.

Run collection in the separate Isaac environment and pass the data interpreter as
`--data-python /path/to/qlm-data-env/bin/python`. The recorder keeps actual Raw
capture/media; the CPU subprocess packages and validates them. No WAM checkout is
required by either step. A failed conversion remains a failed local attempt.

Run conversion or review independently:

```bash
/path/to/qlm-data-env/bin/python -m qlm_bench.cli data convert --raw /path/to/fresh/raw --canonical /path/to/new/canonical --ffmpeg /path/to/ffmpeg --ffprobe /path/to/ffprobe
/path/to/qlm-data-env/bin/python -m qlm_bench.cli data replay --canonical /path/to/canonical --output /path/to/new/replay.html
```

Conversion refuses an existing Raw manifest or Canonical destination. It requires
complete, actual capture boundaries and a pre-reset terminal; it does not consult
historical DATA-004/009 approval records. Demonstration publication and formal
benchmark admission are separate decisions. Previously published episodes are
read through fixed release references and are never passed back through conversion.

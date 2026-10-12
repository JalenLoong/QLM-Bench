"""Use the public opt-in batch runner; no Raw/Canonical outputs are generated."""
from qlm_bench.backends.isaac.batch import main

if __name__ == '__main__':
    raise SystemExit(main())

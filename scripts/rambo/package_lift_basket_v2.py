"""Compatibility CLI for the QLM CPU Raw-to-Canonical converter."""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from qlm_bench.compatibility.dataset_v2.conversion_lift import main

if __name__ == "__main__":
    main()

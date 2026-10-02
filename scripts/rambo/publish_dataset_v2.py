"""Compatibility entrypoint for the original immutable demonstration publisher.

Publication policy/CLI behavior remain in the frozen legacy implementation. The
CPU package provides the shared inventory/hash/readback core for typed stagers.
"""
from pathlib import Path
import sys

# Also support running this repo-local compatibility script before installation.
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'src'))
from qlm_bench.publication.legacy_core import (check_local, describe, digest, main,
    matches, pending_files, remote_files, safe_path, save)

if __name__ == '__main__':
    main()

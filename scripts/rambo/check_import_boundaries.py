#!/usr/bin/env python3
"""Fail if simulator-owned RAMBO code imports WAM packages."""

from __future__ import annotations

import ast
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "source" / "rambo" / "rambo"
FORBIDDEN = {"wam_data", "wam_policy", "wam_rambo", "wam_contracts", "wan_va", "diffusers", "transformers"}


def main() -> int:
    failures: list[str] = []
    for path in list(SOURCE.rglob("*.py")) + list((ROOT / "scripts" / "rambo").rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        roots: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots.update(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                roots.add(node.module.split(".")[0])
        found = sorted(roots & FORBIDDEN)
        if found:
            failures.append(f"{path.relative_to(ROOT)}: forbidden WAM imports {found}")
    # Public CPU modules never depend on the simulator or model stack. The
    # explicitly lazy simulator entry modules retain their own import tests.
    core = ROOT / "src/qlm_bench"
    for path in core.rglob("*.py"):
        if "controllers" in path.relative_to(core).parts:
            for node in ast.walk(ast.parse(path.read_text())):
                names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                        [node.module] if isinstance(node, ast.ImportFrom) and node.module else []
                if any(name.split('.')[0] in FORBIDDEN | {"rambo","crl2","isaaclab","isaacsim","omni","mujoco","mujoco_warp"}
                       or name.startswith("qlm_bench.backends") for name in names):
                    failures.append(f"{path.relative_to(ROOT)}: controller depends on simulator/model")
            continue
        if "backends" in path.relative_to(core).parts or path.relative_to(core).as_posix() in {"collection/isaac.py", "live/isaac.py"}:
            continue
        if path.relative_to(core).as_posix() in {'rl_v2/worker.py','rl_v2/validation.py'}:
            # Explicit opt-in CPU simulation process; importing it remains lightweight.
            tree = ast.parse(path.read_text())
            for node in ast.walk(tree):
                names = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else \
                        [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module else []
                if set(names) & FORBIDDEN:
                    failures.append(f'{path.relative_to(ROOT)}: worker imports model stack')
            for node in tree.body:
                names = [a.name.split('.')[0] for a in node.names] if isinstance(node, ast.Import) else \
                        [node.module.split('.')[0]] if isinstance(node, ast.ImportFrom) and node.module else []
                if set(names) & {'torch', 'mujoco'}:
                    failures.append(f'{path.relative_to(ROOT)}: worker eagerly imports simulation')
            continue
        for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"), filename=str(path))):
            names = [a.name.split(".")[0] for a in node.names] if isinstance(node, ast.Import) else \
                    [node.module.split(".")[0]] if isinstance(node, ast.ImportFrom) and node.module else []
            forbidden = set(names) & (FORBIDDEN | {"rambo", "crl2", "isaaclab", "isaacsim", "omni", "torch"})
            if forbidden:
                failures.append(f"{path.relative_to(ROOT)}: forbidden public CPU imports {sorted(forbidden)}")
    if failures:
        print("RAMBO import-boundary check failed:\n" + "\n".join(failures), file=sys.stderr)
        return 1
    print("RAMBO import boundaries: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

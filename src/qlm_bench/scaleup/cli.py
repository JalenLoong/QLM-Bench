from __future__ import annotations
import argparse
import json
from pathlib import Path
from .contract import make_slots, check_slots
from .source import verify_bindings, freeze_snapshot, apply_snapshot
from qlm_bench.tasks.registration import registrations


def main(argv=None):
    p = argparse.ArgumentParser(prog='qlm scaleup')
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('tasks')
    sub.add_parser('contract')
    slots = sub.add_parser('plan-slots')
    slots.add_argument('--task', choices=tuple(registrations()), required=True)
    slots.add_argument('--asset', action='append', required=True)
    slots.add_argument('--recovery-type', action='append', required=True)
    slots.add_argument('--seed', type=int, required=True)
    slots.add_argument('--output', type=Path, required=True)
    validate = sub.add_parser('validate-slots'); validate.add_argument('plan', type=Path)
    validate.add_argument('--accepted', type=Path)
    bindings = sub.add_parser('bindings'); bindings.add_argument('--source-root', required=True)
    freeze = sub.add_parser('freeze-source'); freeze.add_argument('--source-root', required=True); freeze.add_argument('--output', required=True)
    apply = sub.add_parser('apply-source'); apply.add_argument('--source-root', required=True); apply.add_argument('--snapshot', required=True)
    args = p.parse_args(argv)
    if args.command == 'contract':
        result = json.loads((Path(__file__).with_name('spec') / 'contract.json').read_text())
    elif args.command == 'tasks':
        result = registrations()
    elif args.command == 'plan-slots':
        result = make_slots(args.task, args.asset, seed=args.seed, recovery_types=args.recovery_type)
        check_slots(result)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open('x') as f:
            f.write(json.dumps(result, indent=2) + '\n')
        result = {'passed': True, 'planned_slots': 100, 'output': str(args.output)}
    elif args.command == 'validate-slots':
        result = check_slots(json.loads(args.plan.read_text()), accepted=json.loads(args.accepted.read_text()) if args.accepted else None)
    elif args.command == 'bindings':
        result = verify_bindings(args.source_root)
    elif args.command == 'freeze-source':
        result = freeze_snapshot(args.source_root, args.output)
        result = {key: value for key, value in result.items() if key != 'files'}
    else:
        result = apply_snapshot(args.source_root, args.snapshot)
    print(json.dumps(result, indent=2))
    return 0

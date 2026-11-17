"""Human-approved, LLM-drafted references used to synthesize the QLM-Bench demonstrations.

``workspace/`` mirrors the layout of the original synthesis runs (``runs/audit/<campaign>/...``) so that the
executors resolve their parent classes unchanged.

* ``approved-six-task-bindings.json``: approved executor, recipe, scope, horizon and reference start state of
  each articulated task (sweep, fridge, oven, valve, drawer, door).
* ``workspace/runs/audit/*/``: the executor sources and the approved reference traces / template of push_box,
  press_button, lift_basket and kick_ball_to_goal.

Two locations, two settings:
* ``REFERENCES`` (``@REFERENCES@``): this bundled tree; override with ``QLM_SYNTHESIS_REFERENCES``.
* ``WORKSPACE`` (``@WORKSPACE@``): external inputs that are not bundled (reference runs, scene sources);
  set ``QLM_SYNTHESIS_WORKSPACE``. A ``@WORKSPACE@`` path whose file is bundled resolves to the bundled copy.
"""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCES = Path(os.environ.get('QLM_SYNTHESIS_REFERENCES') or HERE / 'workspace')
WORKSPACE = Path(os.environ['QLM_SYNTHESIS_WORKSPACE']) if os.environ.get('QLM_SYNTHESIS_WORKSPACE') else None
BINDINGS = HERE / 'approved-six-task-bindings.json'


def resolve(value):
    """Expand ``@REFERENCES@`` / ``@WORKSPACE@`` in a path string."""
    if not isinstance(value, str):
        return value
    if value.startswith('@REFERENCES@'):
        return str(REFERENCES) + value[len('@REFERENCES@'):]
    if value.startswith('@WORKSPACE@'):
        rest = value[len('@WORKSPACE@'):]
        if (REFERENCES / rest.lstrip('/')).exists():
            return str(REFERENCES) + rest
        return value if WORKSPACE is None else str(WORKSPACE) + rest
    return value

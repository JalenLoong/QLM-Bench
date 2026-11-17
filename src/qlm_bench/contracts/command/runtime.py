"""native9 command preparation: validate the requested values and produce the executed (force-zero) copy."""
from __future__ import annotations
import copy
import math
import numpy as np
from qlm_bench.contracts.command.validation import (BUNDLE, ContractError, require, validate_command)


def prepare_command(requested, command_id, start_tick):
    """Validate all nine values before producing a non-mutating force-zero copy."""
    require(type(command_id) is str and bool(command_id), 'action', 'command_id')
    require(type(start_tick) is int and 0<=start_tick<=2**63-11 and start_tick%10==0, 'timing','command start')
    try:
        if isinstance(requested,(list,tuple)):
            require(not any(isinstance(x,(bool,np.bool_)) for x in requested),'action','boolean is not a physical action')
        raw=np.asarray(requested)
        require(raw.shape==(9,) and raw.dtype.kind in 'fiu', 'action','nine numeric values required')
        raw=raw.astype(np.float64)
        require(np.isfinite(raw).all() and np.max(np.abs(raw))<=np.finfo(np.float32).max,'action','finite float32-representable values required')
    except (ValueError,TypeError,OverflowError) as error:
        if isinstance(error,ContractError):raise
        raise ContractError('action',error) from error
    # Match the existing setter's dtype; preserve the unquantized request above.
    transformed=raw.astype(np.float32).astype(np.float64);transformed[6:]=0
    result=dict(command_id=command_id,start_tick=start_tick,end_tick=start_tick+10,
                executed_until_tick=start_tick,requested=raw.tolist(),transformed=transformed.tolist(),
                filtered=transformed.tolist(),executed=None,status='not_executed',
                force_overridden=bool(np.any(raw[6:]!=0)),transform_id='native9_force_zero_v2',filter_id='identity',extensions={})
    validate_command(result)
    return result

"""Compatibility route to the independently installed QLM CPU authority.

Original profile/spec identities remain unchanged.
"""
from qlm_bench.compatibility.contracts_v2 import validation as _implementation

globals().update({key: value for key, value in vars(_implementation).items()
                  if not key.startswith("__")})

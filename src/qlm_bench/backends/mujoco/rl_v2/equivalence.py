"""Registered predecessor source identities; excluded from execution_source_identity() because it names
the live digest. An entry maps a predecessor digest (stored in anchors) to the exact successor digests
carrying recorded bitwise evidence (same RGB at every 40-tick boundary, same command receipts) and the
reason. restore accepts a stored predecessor only when the live source is one of its successors, prints
one WARNING and new captures record the live identity. A further edit under the hashed folders must
re-pin tests/qlm/test_rl_v2.py and add its digest here with new evidence; nothing else is accepted."""

EQUIVALENT_SOURCE_IDENTITIES = {
    '95feae2a199082d2a7d81ecc364d43390bd815d36ba55866989e8e94d30ca571': {
        'successors': {'6f7c06212cdabdfe02439b9b25d0a7ff28386fca5bd5672a50c8a5c8ac2ab3ac'},
        'reason': 'QLM-INFRA-006: 42cda63 source of the AMD-prepared pools; the successor only adds the opt-in '
                  'observation_ticks capture cadence and the successor-bound restore gate (render-cadence-20261030 '
                  'evidence)'},
}

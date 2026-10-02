---
id: QLM-ARCHITECTURE
type: guide
status: accepted
source_map: []
---
# Architecture and public interfaces

QLM CPU core owns physical contracts, data/resource discovery and evaluation records.
Isaac backend owns simulation; the retained RAMBO/CRL2 runtime is loaded explicitly.
TaskSpec owns predicates, environment owns clock/outcome/history/terminal, and Recorder
only records events. Collection and evaluation share the environment factory and fixed
controller path. WAM imports only the versioned CPU core, with branch-local adapters.

Public modules: contracts, data, assets, policy_interface, evaluation, collection and
publication. Ordinary imports do not start Kit. Old protocol/grouping lives in frozen
compatibility profiles; model latent/cache/grouping stays outside the physical contract.

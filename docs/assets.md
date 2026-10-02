---
id: QLM-ASSETS
type: guide
status: accepted
source_map: []
---
# Resource identity and preparation

Each asset ID/version maps to a manifest, portable cache subdirectory, entrypoint,
complete reviewed file hashes and source/runtime relationship. Resolver verification
checks the exact expected bytes. Preparation accepts an explicit acquired source and
copies bytes to a new resource cache. It does not invent physics, alter collision geometry
or fall back to private workspace paths. Large original sources remain unchanged until
controlled acquisition and publication gates pass. Runtime shader dependencies and
unconfirmed redistribution are explicit blockers for asset publication, not validation successes.

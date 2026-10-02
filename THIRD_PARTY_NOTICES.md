# Third-party sources

The RAMBO controller/QP/actuator implementation retains its original namespace and
copyright notices, inherited from source commit66605a83180609f610e0dfd23b4440fe91ac689f.
The original CC BY-NC4.0 license is preserved in LICENSE-CC-BY-NC-4.0.md. CRL2 runner
restoration/inference code remains under source/crl2 with its existing notices; removing
training CLI entry points does not change the checkpoint architecture or license.
Isaac Lab/Isaac Sim and their robot assets remain separately installed dependencies,
pinned by the supported runtime locks and source commit. Their licenses are not replaced.

QLM resource manifests separately identify cardboard-box sources, OASIS basket,
industrial/emergency button sources, authorship evidence and derived runtime files.
Existing local use is not a redistribution grant. Controller weights retain their
original external repository/revision/hash rather than being mirrored here. Dataset
releases retain their own published metadata and current unknown license status.

Refactoring changes public packaging, factory/lifecycle boundaries, resource resolution
and tools. Frozen source/data/model artifacts and historical evidence are preserved.

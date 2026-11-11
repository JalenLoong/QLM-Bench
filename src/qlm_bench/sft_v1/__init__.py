"""SFT-v1 (Corrective Task-specific SFT) simulator-side additions.

Nothing here is hashed into ``execution_source_identity()`` (that digest covers controllers/rambo, contracts,
tasks, compatibility/contracts_v2 and backends/mujoco only), so editing the takeover tool or the recovery
routine never invalidates saved RL-v3 own states.
"""

"""Demonstration synthesis: approved executors/references and the libraries to re-generate a demonstration.

A reference (approved trajectory/template for push, press, lift, kick; approved high-level executor for the
six articulated tasks, ``references/``) is executed by the RAMBO controller in MuJoCo with ``trace_only`` physics;
``trace.collect_trace`` records the successful physics trace and ``audit.audit_articulated_trace`` re-checks it.
See ``scripts/synthesis/example_one_demonstration.py``.
"""

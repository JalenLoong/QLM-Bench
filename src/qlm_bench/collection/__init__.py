"""Scripted physical generation. Ordinary imports never initialize a simulator."""
from .orchestrator import CollectionConfig, collect_attempt, source_identity

__all__ = ["CollectionConfig", "collect_attempt", "source_identity"]

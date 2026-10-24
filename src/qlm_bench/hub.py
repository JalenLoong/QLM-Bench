"""Current HF dataset transport; historical DataRef/checkpoint identities stay intact."""

DATASET_REPO_ID = "AIGeeksGroup/QLM-Bench"
LEGACY_DATASET_REPO_ID = "dontKnow23456/QLM-Bench"


def dataset_repo_id(value=DATASET_REPO_ID):
    """Resolve only the owner's confirmed dataset rename, never unrelated repos."""
    return DATASET_REPO_ID if value == LEGACY_DATASET_REPO_ID else value

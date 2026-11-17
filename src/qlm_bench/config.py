"""Site configuration: the only place that names Hugging Face repositories.

Override with environment variables (see ``configs/site.example.env``):
    QLM_DATASET_REPO        dataset repository (default AIGeeksGroup/QLM-Bench)
    QLM_DATASET_REVISION    dataset revision/branch (default release)
"""
import os

DEFAULT_DATASET_REPO_ID = 'AIGeeksGroup/QLM-Bench'


def dataset_repo_id(value=None):
    """Repository to download from: an explicit value, else $QLM_DATASET_REPO, else the default."""
    return value or os.environ.get('QLM_DATASET_REPO') or DEFAULT_DATASET_REPO_ID


def dataset_revision(value=None):
    return value or os.environ.get('QLM_DATASET_REVISION') or 'release'


DATASET_REPO_ID = dataset_repo_id()

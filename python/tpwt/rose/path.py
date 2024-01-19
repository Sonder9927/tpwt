import shutil
from pathlib import Path


def remake(target: str | Path) -> Path:
    """re-make directory
    Re-create the dir given if it exists, or create it.

    Args:
        target (sta|Path): target directory to remake
    Returns:
        Path
    """
    target = Path(target)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)
    return target

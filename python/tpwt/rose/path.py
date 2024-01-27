import shutil
from pathlib import Path


def refile(target: str | Path) -> Path:
    """re-make file
    Re-create the given file if it exists

    Args:
        target (sta|Path): target file to remake
    Returns:
        Path
    """
    target = Path(target)
    if target.exists():
        target.unlink()
    if not target.parent.exists():
        target.parent.mkdir(parents=True)
    return target


def redir(target: str | Path) -> Path:
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

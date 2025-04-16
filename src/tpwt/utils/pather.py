from pathlib import Path


def binuse(command: str, binpath: Path = Path("bin/")) -> Path:
    """get bin command

    Parameters:
        command: target command
        bin_from: relative path

    Returns:
        target path of bin command
    """
    cmdbin = binpath / command
    if not cmdbin.exists():
        err = f"The binary {cmdbin} doesn't exist."
        raise FileNotFoundError(err)
    return cmdbin

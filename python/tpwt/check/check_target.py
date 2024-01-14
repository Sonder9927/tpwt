from pathlib import Path


def check_exists(target) -> Path:
    t = Path(target)
    if t.exists():
        return t
    de = f"Target {target} not found."
    raise FileNotFoundError(de)

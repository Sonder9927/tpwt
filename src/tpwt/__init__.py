from tpwt._core import hello_from_bin
from tpwt.config import ConfigLoader
from tpwt.plot import Ploter


def main() -> None:
    print(hello_from_bin())


__all__ = ["ConfigLoader", "Ploter"]

import tpwt
from pathlib import Path


def test_gen_pathfile():
    tpwt.libtpwt.make_pathfile(
        "tests/data/event.csv", "tests/data/station.csv", "tests/pathfile"
    )


if __name__ == "__main__":
    print(tpwt.libtpwt.hello_from_rust())
    test_gen_pathfile()

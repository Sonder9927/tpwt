from pathlib import Path

from tpwt.inverse.control import calculate_dispersion


def test_calc_disp():
    calculate_dispersion(
        "data/events.csv", "data/stations.csv", Path("outputs/path")
    )


if __name__ == "__main__":
    test_calc_disp()

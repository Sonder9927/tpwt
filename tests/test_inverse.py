from pathlib import Path

from tpwt.inversion.control import calculate_dispersion, aftan_snr
from tpwt.inversion.iterate import make_pre_files


def test_iter_pre():
    make_pre_files(cfg)

def test_aftan_snr():
    aftan_snr(Path("data/SAC"), Path("outputs/path"))


def test_calc_disp():
    calculate_dispersion("data/events.csv", "data/stations.csv", Path("outputs/path"))


if __name__ == "__main__":
    # test_calc_disp()
    # test_aftan_snr()
    test_iter_pre()

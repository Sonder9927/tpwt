from pathlib import Path

import pandas as pd

from tpwt.inversion.filter.tpwt_gmt import gmt_surface


def test_surface():
    ph_csv = Path("outputs/201602171726.20s.ph.csv")
    region = [58.0, 95, 32, 54]
    root_name = ph_csv.parent / ph_csv.stem
    df = pd.read_csv(ph_csv)

    ph_file = root_name.with_suffix(".ph.HD")
    print(ph_file)
    gmt_surface(df[["lon", "lat", "time"]], region, str(ph_file))

    amp_file = root_name.with_suffix(".amp.HD")
    gmt_surface(df[["lon", "lat", "amp"]], region, str(amp_file))


if __name__ == "__main__":
    test_surface()

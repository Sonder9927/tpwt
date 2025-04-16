"""
TPWT Config
"""
from pathlib import Path

import pandas as pd
import tomli
import xarray as xr
from scipy.spatial import ConvexHull


class TPWTConfig:
    """TPWT config"""

    def __init__(self, config_toml: str, greeting: bool = True) -> None:
        """
        create tpwt config

        Parameters:
            config_toml: config file in toml format
            greeting: if print greeting message

        Example:
            ```python
            >>> from tpwt import TPWTConfig
            >>> cfg = TPWTConfig("config.toml")
            ```
        """
        with open(config_toml, "rb") as f:
            config = tomli.load(f)
        self.params = config["parameters"]
        self.paths = {ii: Path(vv) for ii, vv in config["paths"].items()}
        self.outpath = Path("outputs")
        self.outpath.mkdir(exist_ok=True)
        self.model = config["model"]
        self.name = config["model"]["name"]
        if greeting:
            print(
                f"Welcome to TPWT for area `{self.name}`.\nAll loaded from `{config_toml}`."
            )

    def get_params(self, *args):
        return {k: self.params[k] for k in args}

    def region_list(self, expand: float = 0):
        region = self.model["region"]
        return [
            region["west"] - expand,
            region["east"] + expand,
            region["south"] - expand,
            region["north"] + expand,
        ]

    def periods(self) -> list[int]:
        return sorted([i[0] for i in self.model["phvs"]])

    def make_hull(self):
        _make_hull_file(sta_csv=self.paths["sta_csv"])

    def tpwt_path(self):
        control = [
            f"snr{self.params['snr']}",
            f"tmisfit{self.params['tmisfit']}",
            f"nsta{self.params['nsta']}",
            f"nsta_per{str(self.params['nsta_per'])[2:]}",
        ]
        invs = [
            f"smooth{self.params['smooth']}",
            f"damp{str(self.params['damp'])[2:]}",
        ]
        return self.outpath / "_".join(control) / "_".join(invs)


def _make_hull_file(sta_csv: Path):
    dp = sta_csv.parent
    sta = pd.read_csv(sta_csv)
    sta = sta[["longitude", "latitude"]]
    sta.columns = ["x", "y"]
    # sta["x"] = sta["x"].clip(lower=region[0], upper=region[1])
    # sta["y"] = sta["y"].clip(lower=region[-2], upper=region[-1])
    points = sta[["x", "y"]].values
    hull = ConvexHull(points)
    hull_points = points[hull.vertices]
    df = pd.DataFrame(hull_points, columns=["x", "y"])
    df.to_csv(dp / "hull.csv", index=False)
    ds = xr.Dataset(
        {"x_values": ("points", df["x"]), "y_values": ("points", df["y"])},
        coords={
            "x_coords": ("points", df["x"]),
            "y_coords": ("points", df["y"]),
        },
    )
    ds.to_netcdf("data/plot/hull.nc")

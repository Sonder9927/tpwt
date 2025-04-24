"""
TPWT Config
"""

from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import tomli
import xarray as xr
from scipy.spatial import ConvexHull


class TPWTConfig:
    """TPWT config"""

    valid_methods = ["TPWT", "OPWT"]

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

        self.flags = config["flags"]
        self.params = config["parameters"]
        self.model = config["model"]
        self.region = TPWTRegion(self.model["region"], self.model["dgrid"])

        self.paths = {ii: Path(vv) for ii, vv in config["paths"].items()}
        self.outpath = self.paths["output_dir"]
        self.outpath.mkdir(exist_ok=True)

        if greeting:
            print(
                f"Welcome to TPWT for the area: `{self.flags['name']}`.\n"
                f"All loaded from `{config_toml}`."
            )

    def periods(self) -> List[float]:
        return sorted([i[0] for i in self.model["phvs"]])

    def ph_path(self) -> Path:
        return self.outpath / "ph_amp"

    def valid_method(self) -> str:
        # check method
        method = self.flags["method"].upper()
        if method in self.valid_methods:
            return method
        raise ValueError(f"Unvalid method: {method}, pick one in {self.valid_methods}")

    def tpwt_path(self) -> Path:
        control = [
            f"snr{self.params['snr']}",
            f"tmisfit{self.params['tmisfit']}",
            f"nsta{self.params['nsta']}",
            f"valid_ratio{str(self.params['valid_ratio'])[2:]}",
        ]
        invs = [
            f"smooth{self.params['smooth']}",
            f"damp{str(self.params['damp'])[2:]}",
        ]
        return self.outpath / "_".join(control) / "_".join(invs)

    def binuse(self, command: str) -> str:
        """get bin command

        Parameters:
            command: target command
            binpath: relative path

        Returns:
            absolute path of target bin command
        """
        binpath = Path().cwd() / self.paths["binpath"]
        cmdbin = binpath / command
        if cmdbin.exists():
            return str(cmdbin)
        err = f"The binary {cmdbin} doesn't exist."
        raise FileNotFoundError(err)

    def get_disps(self) -> List[str]:
        love = self.paths["utils"] / "LOVE_400_100.disp"
        rayl = self.paths["utils"] / "RAYL_320_80_32000_8000.disp"
        if all([love.exists(), rayl.exists()]):
            return [str(love), str(rayl)]
        raise FileNotFoundError(f"Cant find disp file in {self.paths['utils']}")

    def make_hull(self):
        _make_hull_file(sta_csv=self.paths["sta_csv"])


class TPWTRegion:
    """TPWT Region"""

    def __init__(self, region: Dict[str, float], dgrid: float):
        self.west = region["west"]
        self.east = region["east"]
        self.south = region["south"]
        self.north = region["north"]
        self.dgrid = dgrid

    def to_list(self, expand: float = 0) -> List[float]:
        return [
            self.west - expand,
            self.east + expand,
            self.south - expand,
            self.north + expand,
        ]

    def dgrids(self) -> Tuple[float, float]:
        dgrid = self.dgrid
        return (dgrid, dgrid)


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

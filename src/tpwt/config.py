from pathlib import Path

import tomli
from .math import make_hull_files


class ConfigLoader:
    def __init__(self, config_toml: str, greeting=True) -> None:
        with open(config_toml, "rb") as f:
            config = tomli.load(f)
        self.params = config["parameters"]
        self.paths = {ii: Path(vv) for ii, vv in config["paths"].items()}
        self.model = config["model"]
        self.name = config["model"]["name"]
        if greeting:
            print(
                f"Welcome to TPWT for area `{self.name}`.\nAll loaded from `{config_toml}`."
            )

    def region_list(self):
        region = self.model["region"]
        return [region["west"], region["east"], region["south"], region["north"]]

    def periods(self) -> list[int]:
        return sorted([i[0] for i in self.model["phvs"]])

    def make_hull_files(self):
        make_hull_files(region=self.region_list(), sta_csv=self.paths["sta_csv"])

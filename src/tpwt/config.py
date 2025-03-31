from pathlib import Path

import tomli


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

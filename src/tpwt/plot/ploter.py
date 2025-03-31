from pathlib import Path
from typing import Optional

import pandas as pd

from tpwt import ConfigLoader

from .region import _plot_region


class Ploter:
    def __init__(self, config: ConfigLoader) -> None:
        self.cfg = config
        self.name = self.cfg.name
        self.fig_root = Path("images")
        self.fig_root.mkdir(exist_ok=True)

    def plot_region(self, outfile: Optional[str] = None):
        sta_df = pd.read_csv(self.cfg.paths["sta_csv"])
        fig = _plot_region(self.cfg.name, self.cfg.region_list(), sta_df)
        if not outfile:
            outfile = self._fig_name("region")
        print(f"Saved to `{outfile}`.")
        fig.savefig(outfile)

    def _fig_name(self, suffix: str) -> str:
        out_path = self.fig_root / f"{self.name}_{suffix}.png"
        return str(out_path)

from pathlib import Path
from tqdm import tqdm
from typing import Optional

import pandas as pd

from tpwt import ConfigLoader

from .region import _plot_region
from .phase import _plot_phv


class Ploter:
    def __init__(self, config: ConfigLoader) -> None:
        self.cfg = config
        self.name = self.cfg.name
        self.fig_root = Path("images")
        self.fig_root.mkdir(exist_ok=True)
        Path("temp").mkdir(exist_ok=True)

    def plot_region(self, outfile: Optional[str] = None):
        sta_df = pd.read_csv(self.cfg.paths["sta_csv"])
        fig = _plot_region(self.cfg.region_list(), sta_df)
        if not outfile:
            outfile = self._fig_name("region")
        print(f"Saved to `{outfile}`.")
        fig.savefig(outfile)

    def plot_phase_velocities(self, periods: Optional[list[int]] = None, **kwargs):
        pers = periods or self.cfg.periods()
        with tqdm(total=len(pers)) as pbar:
            for per in pers:
                self.plot_phase_velocity(per, **kwargs)
                pbar.update(1)

    def plot_phase_velocity(
        self,
        period,
        *,
        phv_csv: Optional[str | Path] = None,
        outfile: Optional[str] = None,
        series: Optional[list[float]] = None,
        clip: bool = False,
        ave: bool = False,
    ):
        phv_csv = phv_csv or self.cfg.paths["phv_csv"]
        phv_df = pd.read_csv(
            phv_csv, usecols=["longitude", "latitude", f"phv_{period}"]
        )
        phv_df.columns = ["x", "y", "z"]
        fig = _plot_phv(
            phv_df,
            period,
            self.cfg.region_list(),
            series=series,
            clip=clip,
            ave=ave,
        )
        if not outfile:
            outfile = self._fig_name(f"phv_{period}s", ave)
        print(f"Saved to `{outfile}`.")
        fig.savefig(outfile)

    def _fig_name(self, suffix: str, ave: bool) -> str:
        out_path = self.fig_root / f"{self.name}_{suffix}.png"
        if ave:
            out_path = out_path.with_suffix(".ave.png")
        return str(out_path)

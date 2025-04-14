from pathlib import Path
from typing import Optional

import pandas as pd
from tqdm import tqdm

from tpwt import TPWTConfig

from .phase import plot_diff_fig, plot_phv_fig
from .region import plot_region_fig


class Ploter:
    def __init__(self, config: TPWTConfig) -> None:
        self.cfg = config
        self.name = self.cfg.name
        self.fig_root = Path("images")
        self.fig_root.mkdir(exist_ok=True)
        self.region: list[float] = self.cfg.region_list()
        Path("temp").mkdir(exist_ok=True)

    def plot_region(self, outfile: Optional[str] = None):
        sta_df = pd.read_csv(self.cfg.paths["sta_csv"])
        fname = outfile or self._fig_name("region")
        plot_region_fig(sta_df, self.region, fname)

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
        fname = outfile or self._fig_name(f"phv_{period}s", ave)
        plot_phv_fig(phv_df, self.region, period, fname, series, clip, ave)

    def plot_diff(
        self,
        period,
        csv1: str,
        csv2: Optional[str | Path] = None,
        *,
        outfile: Optional[str] = None,
        ave: bool = False,
        clip: bool = False,
        series: Optional[list[float]] = None,
    ):
        df1 = pd.read_csv(csv1, usecols=["longitude", "latitude", f"phv_{period}"])
        df1.columns = ["x", "y", "z"]
        csv2 = csv2 or self.cfg.paths["phv_csv"]
        df2 = pd.read_csv(csv2, usecols=["longitude", "latitude", f"phv_{period}"])
        df2.columns = ["x", "y", "z"]
        fname = outfile or self._fig_name("diff", ave)
        plot_diff([df1, df2], self.region, period, fname, series, clip, ave)

    def _fig_name(self, suffix: str, ave: bool = False) -> str:
        out_path = self.fig_root / f"{self.name}_{suffix}.png"
        if ave:
            out_path = out_path.with_suffix(".ave.png")
        return str(out_path)

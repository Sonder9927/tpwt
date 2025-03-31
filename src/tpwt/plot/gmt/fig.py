from pathlib import Path

import pandas as pd

from .make_data import area_clip


class GmtFigger:
    gra = None
    data = Path("data")

    def __init__(self, fig, topo, *, projection=None, frame=None):
        self.fig = fig
        self.region = topo["region"]
        if frame is None:
            frame = "a"
        # basemap and topo
        self.fig.basemap(
            region=self.region,
            projection=projection or self.hscale(self.region),
            frame=frame,
        )
        if gra := topo.get("gra"):
            self.fig.grdimage(grid=topo["grd"], cmap=topo["cpt"], shading=gra)
            self.gra = gra

    @staticmethod
    def hscale(region: list) -> str:
        # projection
        x = (region[0] + region[1]) / 2
        y = (region[2] + region[3]) / 2
        return f"m{x}/{y}/0.4i"

    def _fig_basalts(self):
        from .make_data import makecpt

        age_limit = 10
        basalts = pd.read_csv(self.data / "tects/China_basalts_data.csv")
        # filter by age
        basalts = basalts[basalts["age"] < age_limit]
        cc = "temp/temp.cpt"
        cc = makecpt([0, age_limit], cmap="hot", reverse=True)
        self.fig.plot(data=basalts[["x", "y", "age"]], style="c0.2c", cmap=cc)
        self.fig.colorbar(
            cmap=cc,
            frame=["a", 'x+l"Volcanic Age (Ma)"'],
            position="JMR+o0.3c/0c+w4.5c",
        )

    def _fig_stations(self):
        stas = pd.read_csv(self.data / "data_nz/station.csv", usecols=[1, 2])
        self.fig.plot(data=stas, style="t0.15c", fill="darkblue")

    def _fig_xenoliths(self):
        # nushan
        self.fig.plot(x=118.09, y=32.8, style="ksquaroid/0.4c", fill="magenta")
        # xinchang
        self.fig.plot(x=120.88, y=29.5, style="ksquaroid/0.4c", fill="magenta")

    def tomos(self, tomos: list[dict], *, clip=None):
        for tomo in tomos:
            if clip:
                tomo["grid"] = area_clip(tomo["grid"], hull="data/plot/hull.nc", region=self.region)
            self.fig.grdimage(**tomo, shading=self.gra, nan_transparent=True)

    def tects(self, plot_id: int | None, text_file: str | None):
        # plot tects and elements like sta basalt volcano
        # notice that tect is int, which may be 0 meaning False
        tects_dir = self.data / "tects"
        if plot_id is not None:
            self.fig.coast(shorelines="1/0.5p,black")
            # tectonics
            geo_data = ["China_tectonic.dat", "CN-faults.gmt", "find.gmt"]
            pens = ["1p,black,-", "0.5p,black,-"]
            self.fig.plot(data=tects_dir / geo_data[plot_id], pen=pens[0])
            # self.fig.plot(data=tects_dir / "small_faults.gmt", pen=pens[1])
            # fig.plot(data=tects_dir / "faults_finding.gmt", pen="red")  # noqa: ERA001

        # text
        if text_file:
            self.fig.text(
                textfiles=tects_dir / text_file, angle=True, font=True, justify=True
            )

    def eles(self, eles):
        fig_ele_funcs = {
            "sta": self._fig_stations,
            "basalt": self._fig_basalts,
            "xenolith": self._fig_xenoliths,
        }
        for e in eles:
            if e not in fig_ele_funcs:
                message = rf"`{e}` is not implemented, choose in {fig_ele_funcs.keys()}"
                raise KeyError(message)
            fig_ele_funcs[e]()

    def lines(self, lines, pen):
        for line in lines:
            self.fig.plot(data=line, pen=pen)


def fig_tomos(
    fig,
    topo,
    tomos,
    *,
    frame=None,
    projection=None,
    clip=False,
    tect: tuple[int | None, str | None] = (None, None),
    eles=(),
    lines=(),
    line_pen="black",
):
    gf = GmtFigger(fig, topo, frame=frame, projection=projection)
    gf.tomos(tomos, clip=clip)
    if tect:
        gf.tects(tect[0], tect[1])
    gf.eles(eles)
    gf.lines(lines, line_pen)

    return gf.fig

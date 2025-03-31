import pygmt

from .gmt.make_data import (
    make_topos,
    area_clip,
    makecpt,
    auto_series,
    mean_over_clipped,
    tomo_grid,
)


def _plot_phv(df, period, region, *, clip, ave, series):
    # make topo
    topo = make_topos("ETOPO1", region)
    # make tomo
    if ave:
        df = mean_over_clipped(df, hull="data/plot/hull.nc")
    tomo = {
        # make grd
        "grid": "temp/temp.grd",
        # make cpt
        "cmap": makecpt(series=series or auto_series(df, method=0)),
    }
    tomo_grid(df, region, tomo["grid"])

    # plot fig
    fig = pygmt.Figure()
    pygmt.config(MAP_FRAME_TYPE="plain")
    fig.basemap(
        region=region,
        projection=_hscale(region),
        frame=["a"],
    )
    fig.grdimage(grid=topo["grd"], cmap=topo["cpt"], shading=topo["gra"])
    if clip:
        tomo["grid"] = area_clip(tomo["grid"], hull="data/plot/hull.nc", region=region)
    fig.grdimage(**tomo, nan_transparent=True)
    fig.coast(shorelines="0.5p")

    fig.text(
        x=region[0],
        y=region[-1],
        fill="white",
        justify="LT",
        font="9p",
        text=f"{period}s",
        offset="0.1",
    )
    fig.colorbar(cmap=tomo["cmap"], frame=["a", "x+lPhase Velocity", "y+lkm/s"])

    return fig


def _hscale(region: list) -> str:
    # projection
    x = (region[0] + region[1]) / 2
    y = (region[2] + region[3]) / 2
    return f"m{x}/{y}/0.4i"

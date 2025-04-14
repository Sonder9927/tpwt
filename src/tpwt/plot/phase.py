import pygmt
import pandas as pd

from .gmt.fig import fig_tomos
from .gmt.make_data import (
    make_topos,
    area_clip,
    makecpt,
    auto_series,
    mean_over_clipped,
    tomo_grid,
)


def plot_diff_fig(dfs, region, period, fname: str, series, clip, ave):
    tomos, diff_df = _diff_tomos(dfs, region, period, series, ave)
    _diff_fig(tomos, diff_df, region=region, period=period, fname=fname, clip=clip)


def _diff_tomos(dfs, region, period, series, ave):
    # cpt file
    cptfile = "temp/tomo.cpt"
    diffcpt = "data/plot/cptfiles/vs_dif.cpt"
    tomos = {
        "tomo1": {"grid": "temp/grd1.grd", "cmap": cptfile},
        "tomo2": {"grid": "temp/grd2.grd", "cmap": cptfile},
        "tomodiff": {"grid": "temp/grddiff.grd", "cmap": diffcpt},
    }
    pers_series = {
        "20": [3.45, 3.61, 0.02],
        "25": [3.63, 3.76, 0.02],
        "30": [3.7, 3.85, 0.02],
        "50": [3.73, 3.88, 0.02],
        "60": [3.75, 3.9, 0.02],
    }
    series = series or pers_series.get(period)
    grd1 = tomo_grid(dfs[0], region, tomos["tomo1"]["grid"])
    grd2 = tomo_grid(dfs[1], region, tomos["tomo2"]["grid"])

    # make diff grid
    merged = pd.merge(grd1, grd2, on=["x", "y"], how="left")
    merged["z"] = (merged["z_x"] - merged["z_y"]) * 1000
    diff_df = merged[["x", "y", "z"]]
    tomo_grid(diff_df, region, tomos["tomodiff"]["grid"])
    if ave:
        makecpt([-4.5, 4.5, 1], cptfile)
        df1_ave = mean_over_clipped(dfs[0])
        df2_ave = mean_over_clipped(dfs[1])
        tomo_grid(df1_ave, region, tomos["tomo1"]["grid"])
        tomo_grid(df2_ave, region, tomos["tomo2"]["grid"])
    else:
        makecpt(series, cptfile)
    return tomos, diff_df


def _diff_fig(tomos, diff_df, region, period, fname, clip):
    topo = make_topos("ETOPO1", region)
    tomo1 = tomos["tomo1"]
    tomo2 = tomos["tomo2"]
    tomodiff = tomos["tomodiff"]
    # gmt plot
    fig = pygmt.Figure()
    # define figure configuration
    pygmt.config(MAP_FRAME_TYPE="plain")
    with fig.subplot(
        nrows=2, ncols=2, figsize=("15c", "14.5c"), autolabel=False, margins="0.5c/0.3c"
    ):
        kws = {"projection": "M?", "clip": clip, "tect": (0, None)}
        # grd1
        with fig.set_panel(panel=0):
            fig = fig_tomos(fig, topo, [tomo1], **kws)
            fig.text(
                x=region[0],
                y=region[-1],
                fill="white",
                justify="LT",
                font="10p",
                text="(a) ASWMS",
                offset="j0.1",
            )
        # tpwt
        with fig.set_panel(panel=1):
            fig = fig_tomos(fig, topo, [tomo2], **kws)
            fig.text(
                x=region[0],
                y=region[-1],
                fill="white",
                justify="LT",
                font="10p",
                text="(b) TPWT",
                offset="j0.1",
            )
            frame = r'xaf+l"Phase Velocity Anomaly (%)"'
            fig.colorbar(
                cmap=tomo1["cmap"], position="JMR+w6c/0.4c+o0.5c/0c", frame=frame
            )
        # diff
        with fig.set_panel(panel=2):
            kws["tect"] = (0, "simpleTectName.txt")
            kws["eles"] = ("xenolith",)
            fig = fig_tomos(fig, topo, [tomodiff], **kws)
            fig.text(
                x=region[0],
                y=region[-1],
                fill="white",
                justify="LT",
                font="10p",
                text="(c) DIFF",
                offset="j0.1",
            )
        # statistics
        with fig.set_panel(panel=3):
            fig.histogram(
                data=diff_df,
                projection="X?",
                frame='y+l"Percentage (%)"',
                region=[-150, 150, 0, 30],
                series=[-150, 150, 20],
                cmap=tomodiff["cmap"],
                histtype=1,  # for frequency percent
                pen="1p,black",
            )
            fig.text(
                x=-150,
                y=30,
                justify="LT",
                font="12p",
                text=f"(d) mean={round(diff_df.mean(), 2)}m/s",
                offset="j0.1",
            )
            fig.text(
                x=-120,
                y=28,
                justify="LT",
                font="12p",
                text=f"std = {round(diff_df.std(), 2)}m/s",
                offset="j0.1",
            )
            frame = r'xa50f50+l"Phase velocity Difference (m/s)"'
            fig.colorbar(
                cmap=tomodiff["cmap"], position="JMR+o0.5c/0c+w6c/0.4c", frame=frame
            )
    fig.savefig(fname)
    print(f"Saved fig -> {fname}")


def plot_phv_fig(df, region, period, fname: str, series, clip, ave):
    tomo = _phv_grds(df, region, series, ave)
    _phv_fig(tomo, region=region, period=period, fname=fname, clip=clip)


def _phv_fig(tomo, region, period, fname, clip):
    # make topo
    topo = make_topos("ETOPO1", region)
    # plot fig
    fig = pygmt.Figure()
    pygmt.config(MAP_FRAME_TYPE="plain")
    fig.basemap(region=region, projection=_hscale(region), frame=["a"])
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
        offset="j0.1",
    )
    fig.colorbar(cmap=tomo["cmap"], frame=["a", "x+lPhase Velocity", "y+lkm/s"])

    # savefig
    fig.savefig(fname)
    print(f"Saved fig -> {fname}")


def _phv_grds(df, region, series, ave):
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
    return tomo


def _hscale(region: list) -> str:
    # projection
    x = (region[0] + region[1]) / 2
    y = (region[2] + region[3]) / 2
    return f"m{x}/{y}/0.4i"


# def _make_diff_grds(period, dfs, region, cptfile, grds, ave):
#     pers_series = {
#         "20": [3.45, 3.61, 0.02],
#         "25": [3.63, 3.76, 0.02],
#         "30": [3.7, 3.85, 0.02],
#         "50": [3.73, 3.88, 0.02],
#         "60": [3.75, 3.9, 0.02],
#     }
#     series = pers_series.get(period)
#     grd1 = tomo_grid(dfs[0], region, grds["grd1"])
#     grd2 = tomo_grid(dfs[1], region, grds["grd2"])

#     # make diff grid
#     merged = pd.merge(grd1, grd2, on=["x", "y"], how="left")
#     merged["z"] = (merged["z_x"] - merged["z_y"]) * 1000
#     diff = merged[["x", "y", "z"]]
#     tomo_grid(diff, region, grds["diff"])
#     if ave:
#         makecpt([-4.5, 4.5, 1], cptfile)
#         grd1 = mean_over_clipped(grd1, hull="data/plot/hull.nc")
#         grd2 = mean_over_clipped(grd2, hull="data/plot/hull.nc")
#         tomo_grid(grd1, region, grds["grd1"])
#         tomo_grid(grd2, region, grds["grd2"])
#     else:
#         makecpt(series, cptfile)
#     return diff


# def _plot_diff_grds(diff, grds, region, cpt, fname, ave):
#     topo = make_topos("ETOPO1", region)
#     diff = area_clip(diff, hull="data/plot/hull.nc")["z"]
#     # gmt plot
#     fig = pygmt.Figure()
#     # define figure configuration
#     pygmt.config(MAP_FRAME_TYPE="plain")
#     with fig.subplot(
#         nrows=2, ncols=2, figsize=("15c", "14.5c"), autolabel=False, margins="0.5c/0.3c"
#     ):
#         kws = {"projection": "M?", "clip": True, "tect": (0, None)}
#         # grd1
#         with fig.set_panel(panel=0):
#             tomo = {"grid": grds["grd1"], "cmap": cpt}
#             fig = fig_tomos(fig, topo, [tomo], **kws)
#             fig.text(
#                 x=region[0],
#                 y=region[-1],
#                 fill="white",
#                 justify="LT",
#                 font="10p",
#                 text="(a) ASWMS",
#                 offset="j0.1",
#             )
#         # tpwt
#         with fig.set_panel(panel=1):
#             tomo["grid"] = grds["grd2"]
#             fig = fig_tomos(fig, topo, [tomo], **kws)
#             fig.text(
#                 x=region[0],
#                 y=region[-1],
#                 fill="white",
#                 justify="LT",
#                 font="10p",
#                 text="(b) TPWT",
#                 offset="j0.1",
#             )
#             frame = r'xaf+l"Phase Velocity Anomaly (%)"'
#             fig.colorbar(cmap=cpt, position="JMR+w6c/0.4c+o0.5c/0c", frame=frame)
#         # diff
#         with fig.set_panel(panel=2):
#             cdf = "data/plot/cptfiles/vs_dif.cpt"
#             tomo = {"grid": grds["diff"], "cmap": cdf}
#             kws["tect"] = (0, "simpleTectName.txt")
#             kws["eles"] = ("xenolith",)
#             fig = fig_tomos(fig, topo, [tomo], **kws)
#             fig.text(
#                 x=region[0],
#                 y=region[-1],
#                 fill="white",
#                 justify="LT",
#                 font="10p",
#                 text="(c) DIFF",
#                 offset="j0.1",
#             )
#         # statistics
#         with fig.set_panel(panel=3):
#             fig.histogram(
#                 data=diff,
#                 projection="X?",
#                 frame='y+l"Percentage (%)"',
#                 region=[-150, 150, 0, 30],
#                 series=[-150, 150, 20],
#                 cmap=cdf,
#                 histtype=1,  # for frequency percent
#                 pen="1p,black",
#             )
#             fig.text(
#                 x=-150,
#                 y=30,
#                 justify="LT",
#                 font="12p",
#                 text=f"(d) mean={round(diff.mean(), 2)}m/s",
#                 offset="j0.1",
#             )
#             fig.text(
#                 x=-120,
#                 y=28,
#                 justify="LT",
#                 font="12p",
#                 text=f"std = {round(diff.std(), 2)}m/s",
#                 offset="j0.1",
#             )
#             frame = r'xa50f50+l"Phase velocity Difference (m/s)"'
#             fig.colorbar(cmap=cdf, position="JMR+o0.5c/0c+w6c/0.4c", frame=frame)
#     fig.savefig(fname)
#     print(f"Saved fig -> {fname}")

import pandas as pd
import pygmt


def plot_region_fig(sta_df, region, fname: str):
    fig = pygmt.Figure()
    pygmt.config(MAP_FRAME_TYPE="plain")
    fig.basemap(
        region=region,
        projection="M15c",
        frame=["a1"],
        # frame=["a1", f"+t{name}"],
    )
    fig.grdimage("@earth_relief_15s", cmap="geo", shading=True, transparency=30)
    fig.coast(
        borders=["1/0.5p,black"],
        # shorelines="0.5p,blue",
        water="lightblue",
        area_thresh=1000,
    )
    # fig.plot(data="@nz_faults.gmt", pen="1p,black", transparency=40)
    # stations
    sta_unique = sta_df["ide"].unique()
    symbols = pd.read_csv("data/plot/symbols.csv", index_col="label")
    for ide in sta_unique:
        istas = sta_df[sta_df["ide"] == ide]
        fig.plot(
            x=istas["longitude"],
            y=istas["latitude"],
            style=symbols["style"][ide],
            pen=symbols["pen"][ide],
            fill=symbols["fill"][ide],
            label=f"{ide}+S0.25c",
        )
    # fig.colorbar(frame=["a1000", "x+lElevation", "y+lm"])
    fig.legend(transparency=30)
    fig.savefig(fname)
    print(f"Saved fig -> {fname}")

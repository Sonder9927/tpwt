from pathlib import Path

import pandas as pd
import pygmt


def auto_series(grid: str | pd.DataFrame, method=0, hull=None):
    if isinstance(grid, str):
        grid: pd.DataFrame = pd.read_csv(grid, delim_whitespace=True, header=None)
    grid.columns = ["x", "y", "z"]
    if hull is not None:
        grid: pd.DataFrame = area_clip(grid, hull)
    avg = grid["z"].mean()
    min_val = grid["z"].min()
    max_val = grid["z"].max()
    if method == 0:
        return [min_val, max_val, 0.03]
    if method == 1:
        dev = min([avg - min_val, max_val - avg])
        return [avg - dev + 0.03, avg + dev - 0.03, 0.03]
    dev = max([avg - min_val, max_val - avg])
    return [avg - dev + 0.02, avg + dev - 0.02, 0.03]


###############################################################################
def make_topos(
    idt,
    region,
    *,
    data="data/plot/tects/ETOPO1.grd",
    normalize="t",
    resolution=None,
    cmap="grayC",
    series=None,
):
    if series is None:
        series = [-50000, 5000]
    temp = Path("temp")
    ctopo = str(temp / f"topo_{cmap}.cpt")
    grd = temp / f"topo_{idt}.grd"
    gra = temp / f"topo_{idt}.gradient"
    topos = dict(
        zip(
            ["grd", "gra", "cpt", "region"],
            [grd, gra, makecpt(series, ctopo, cmap=cmap), region],
        )
    )
    if Path(gra).exists():
        return topos
    TOPO_CUT = "temp/topo_cut.grd"
    TOPO_SAMPLE = "temp/topo_sample.grd"
    if resolution:
        data = pygmt.datasets.load_earth_relief(
            resolution=resolution, region=region, registration="gridline"
        )
    # grdcut
    pygmt.grdcut(
        grid=data,
        region=region,
        outgrid=TOPO_CUT,
    )
    # grdsample
    pygmt.grdsample(
        grid=TOPO_CUT,
        outgrid=TOPO_SAMPLE,
        region=region,
        spacing=0.01,
        # translate=True,
    )
    TOPO_GRA = "temp/topo.gradient"
    # grdgradient
    pygmt.grdgradient(
        grid=TOPO_SAMPLE,
        outgrid=TOPO_GRA,
        azimuth=45,
        normalize=normalize,
        verbose="w",
    )
    Path(TOPO_SAMPLE).rename(grd)
    Path(TOPO_GRA).rename(gra)
    return topos


###############################################################################
def makecpt(
    series, output="temp/temp.cpt", cpt="C-redBlue.cpt", reverse=False, cmap=None
) -> str:
    cpts = Path("data/plot/cptfiles")
    cmap = cmap or str(cpts / cpt)
    pygmt.makecpt(
        cmap=cmap,
        series=series,
        output=output,
        continuous=True,
        background=True,
        reverse=reverse,
    )
    return output


###############################################################################
def tomo_grid(data, region, outfile=None, **spacings) -> pd.DataFrame:
    if spacings is None:
        spacings = {}
    # blockmean
    xyz = pygmt.blockmean(
        data=data, region=region, spacing=spacings.get("blockmean", 0.5), nodata="-9999"
    )
    # surface
    grd = pygmt.surface(
        data=xyz, region=region, spacing=spacings.get("surface", 0.5), nodata="-9999"
    )
    # grdsample
    if outfile is not None:
        pygmt.grdsample(
            grid=grd, spacing=spacings.get("grdsample", 0.01), outgrid=outfile
        )
    return pygmt.grd2xyz(grd)


###############################################################################
def mean_over_clipped(data, hull) -> pd.DataFrame:
    clipped_df = area_clip(data, hull)
    mm = clipped_df["z"].mean()
    data["z"] = (data["z"] - mm) / mm * 100
    return data


def area_clip(data, hull: str, *, region=None, spacing=0.01) -> pd.DataFrame:
    if not Path(hull).exists():
        raise FileNotFoundError(f"No file: {hull}")

    if isinstance(data, str):
        data = pygmt.grd2xyz(data)
    clipped_data = pygmt.select(data, polygon=hull)
    if clipped_data is None:
        raise ValueError("Nothing were selected.")
    if region is not None:
        return pygmt.xyz2grd(data=clipped_data, region=region, spacing=spacing)
    return clipped_data


def clipped_df(df, hull, *, region=None, ave=False):
    if ave:
        return mean_over_clipped(df, hull)
    else:
        return area_clip(df, hull, region=region)

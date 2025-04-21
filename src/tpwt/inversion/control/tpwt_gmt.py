from pathlib import Path

import pandas as pd
import pygmt


def gmt_surface(data, region: list, outfile: str):
    data.names = ["x", "y", "z"]
    grid = pygmt.surface(data=data, spacing=0.2, region=region)
    pygmt.grd2xyz(grid=grid, region=region, outfile=outfile)


# plot phase time
def gmt_phase_time(data, region: list, outfile: str):
    data.names = ["x", "y", "z"]
    grid = pygmt.surface(
        data=data,
        spacing=0.2,
        region=region,
    )
    pygmt.grd2xyz(grid=grid, region=region, output_type="file", outfile=outfile)


# plot amp
def gmt_amp(data, region: list, outfile: str):
    data.names = ["x", "y", "z"]
    grid = pygmt.surface(
        data=data,
        spacing=0.2,
        region=region,
    )
    pygmt.grd2xyz(
        grid=grid, region=region, output_type="file", outfile=f"{output_am}.HD"
    )

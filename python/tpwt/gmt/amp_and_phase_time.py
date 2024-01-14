from pathlib import Path
import pandas as pd
import pygmt


# plot phase time
def gmt_phase_time(input_map, region: list):
    im = str(input_map)
    grid = pygmt.surface(
        data=im,
        spacing=0.2,
        region=region,
    )
    pygmt.grd2xyz(
        grid=grid, region=region, output_type="file", outfile=f"{im}.HD"
    )


# plot amp
def gmt_amp(input_map: Path, region: list):
    parts = input_map.name.split(".")
    parts[1] = "_am."
    output_am: str = str(Path(input_map.parent) / "".join(parts))

    df = pd.read_csv(
        input_map,
        delim_whitespace=True,
        usecols=[0, 1, 4],
        header=None,
        engine="python",
    )
    df.to_csv(output_am, sep=" ", header=False, index=False)

    grid = pygmt.surface(
        data=output_am,
        spacing=0.2,
        region=region,
    )
    pygmt.grd2xyz(
        grid=grid, region=region, output_type="file", outfile=f"{output_am}.HD"
    )

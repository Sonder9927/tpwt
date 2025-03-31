import math
import operator
from functools import reduce
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
from scipy.spatial import ConvexHull
from shapely.geometry import Point, Polygon


def make_hull_files(region, sta_csv: Path):
    dp = sta_csv.parent
    sta = pd.read_csv(sta_csv)
    sta = sta[["longitude", "latitude"]]
    sta.columns = ["x", "y"]
    # sta["x"] = sta["x"].clip(lower=region[0], upper=region[1])
    # sta["y"] = sta["y"].clip(lower=region[-2], upper=region[-1])
    points = sta[["x", "y"]].values
    hull = ConvexHull(points)
    hull_points = points[hull.vertices]
    df = pd.DataFrame(hull_points, columns=["x", "y"])
    df.to_csv(dp / "hull.csv", index=False)
    ds = xr.Dataset(
        {"x_values": ("points", df["x"]), "y_values": ("points", df["y"])},
        coords={
            "x_coords": ("points", df["x"]),
            "y_coords": ("points", df["y"]),
        },
    )
    ds.to_netcdf("data/plot/hull.nc")


def area_hull_files(region, outdir) -> None:
    sta_file = "data/station.lst"
    sta = pd.read_csv(sta_file, delim_whitespace=True, usecols=[1, 2], names=["x", "y"])
    sta["x"] = sta["x"].clip(lower=region[0], upper=region[1])
    sta["y"] = sta["y"].clip(lower=region[-2], upper=region[-1])
    points = sta[["x", "y"]].values
    hull = ConvexHull(points)
    hull_points = points[hull.vertices]
    df = pd.DataFrame(hull_points, columns=["x", "y"])
    df.to_csv(outdir / "area_hull.csv", index=False)
    ds = xr.Dataset(
        {"x_values": ("points", df["x"]), "y_values": ("points", df["y"])},
        coords={
            "x_coords": ("points", df["x"]),
            "y_coords": ("points", df["y"]),
        },
    )
    ds.to_netcdf(outdir / "area_hull.nc")


###############################################################################


# def times_of_crossing_boundary(point: Point, points: list[Point]) -> int:
#     times = 0
#     for i in range(len(points)):
#         segment_start = points[i]
#         segment_end = points[0] if i == len(points) - 1 else points[i + 1]
#         if point.is_ray_intersects_segment(segment_start, segment_end):
#             times += 1

#     return times


def clock_sorted(points):
    center = tuple(
        map(
            operator.truediv,
            reduce(lambda x, y: map(operator.add, x, y), points),
            [len(points)] * 2,
        )
    )
    return sorted(
        points,
        key=lambda p: (
            -135 - math.degrees(math.atan2(*tuple(map(operator.sub, p, center))[::-1]))
        )
        % 360,
        reverse=True,
    )


def points_boundary(data: pd.DataFrame, region=None, clock=False):
    """
    Get the boundary of points getted from the file.
    """
    if region is not None:
        data["x"].clip(lower=region[0], upper=region[1])
        data["y"].clip(lower=region[-2], upper=region[-1])
    data = np.array(data)
    hull = ConvexHull(data)
    points = data[hull.vertices]
    if clock:
        points = clock_sorted(points)

    return points


def points_inner(data, border):
    points = border[["x", "y"]].values
    hull = ConvexHull(points)
    polygon = Polygon(points[hull.vertices])
    ids = data.apply(lambda r: Point(r["x"], r["y"]).within(polygon), axis=1)

    return data[ids]


# def points_inner(data: pd.DataFrame, boundary) -> pd.DataFrame:
#     lo = [i[0] for i in boundary]
#     la = [i[1] for i in boundary]

#     points_in_rect = data[
#         (data["y"] < max(la))
#         & (data["y"] > min(la))
#         & (data["x"] < max(lo))
#         & (data["x"] > min(lo))
#     ].copy()

#     boundary_points: list[Point] = [Point(p.tolist()) for p in boundary]

#     points_in_rect["times"] = points_in_rect.apply(
#         lambda dd: times_of_crossing_boundary(
#             Point(x=dd.loc["x"], y=dd.loc["y"]), boundary_points
#         ),
#         axis=1,
#     )
#     data = points_in_rect[points_in_rect["times"] % 2 == 1].drop(
#         columns=["times"]
#     )

#     return data

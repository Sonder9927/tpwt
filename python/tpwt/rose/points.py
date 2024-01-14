import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from tpwt import rs


def times_of_crossing_boundary(point: rs.Point, points: list[rs.Point]) -> int:
    times = 0
    for i in range(len(points)):
        segment_start = points[i]
        segment_end = points[0] if i == len(points) - 1 else points[i + 1]
        if point.is_ray_intersects_segment(segment_start, segment_end):
            times += 1

    return times


###############################################################################


def points_boundary(grids: pd.DataFrame):
    """
    Get the boundary of points getted from the file.
    """
    points = np.array(grids)
    hull = ConvexHull(points)

    return points[hull.vertices]


def points_inner(data: pd.DataFrame, boundary) -> pd.DataFrame:
    lo = [i[0] for i in boundary]
    la = [i[1] for i in boundary]

    points_in_rect = data[
        (data["y"] < max(la))
        & (data["y"] > min(la))
        & (data["x"] < max(lo))
        & (data["x"] > min(lo))
    ].copy()

    boundary_points = [rs.Point(p.tolist()) for p in boundary]

    points_in_rect["times"] = points_in_rect.apply(
        lambda dd: times_of_crossing_boundary(
            rs.Point(x=dd.loc["x"], y=dd.loc["y"]), boundary_points
        ),
        axis=1,
    )
    data = points_in_rect[points_in_rect["times"] % 2 == 1].drop(columns=["times"])

    return data

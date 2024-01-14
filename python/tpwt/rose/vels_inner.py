from icecream import ic
import numpy as np
import pandas as pd
from scipy.spatial import ConvexHull
from tpwt_p.check import check_exists
from tpwt_r import Point


def clock_sorted(points):
    from functools import reduce
    import math, operator

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
            -135
            - math.degrees(
                math.atan2(*tuple(map(operator.sub, p, center))[::-1])
            )
        )
        % 360,
        reverse=True,
    )


def boundary_points(f):
    stas = pd.read_csv(
        f,
        delim_whitespace=True,
        header=None,
        usecols=[1, 2],
        names=["lo", "la"],
    )
    points = np.array(stas[["lo", "la"]])
    hull = ConvexHull(points)

    return points[hull.vertices]


def times_of_crossing_boundary(point, points):
    times = 0
    for i in range(len(points)):
        segment_start = points[i]
        segment_end = points[0] if i == len(points) - 1 else points[i + 1]
        if point.is_ray_intersects_segment(segment_start, segment_end):
            times += 1

    return times


def points_inner(grid_file, points: list):
    vels: pd.DataFrame = pd.read_csv(
        grid_file, delim_whitespace=True, names=["lo", "la", "vel"]
    )
    lo = [i.lo for i in points]
    la = [i.la for i in points]
    vels_in_rect: pd.DataFrame = vels[
        (vels["la"] < max(la))
        & (vels["la"] > min(la))
        & (vels["lo"] < max(lo))
        & (vels["lo"] > min(lo))
    ]
    # ic(len(vels_in_rect))
    total_avg = vels.vel.mean()
    rect_avg = vels_in_rect.vel.mean()
    ic(total_avg, rect_avg)

    point_inner = []
    for i in vels_in_rect.index:
        point = Point(vels_in_rect.lo[i], vels_in_rect.la[i])

        times = times_of_crossing_boundary(point, points)
        if times % 2 == 1:
            point_inner.append([point, vels_in_rect.vel[i]])

    return pd.DataFrame(
        data=[[i[0].lo, i[0].la, i[1]] for i in point_inner],
        columns=["lo", "la", "vel"],
    )


def average_inner(grid_dir, ps):
    tp = type(ps)
    if tp == list:
        bp = ps
    elif tp == str:
        ps = check_exists(ps)
        bp = boundary_points(ps)
    else:
        raise ValueError(
            "Unvalid input points. Please give a list or a string."
        )

    # po = clock_sorted(boundary_points)  # no need

    points = [Point(p[0], p[1]) for p in bp]
    data = points_inner(grid_dir, points)
    # ic(data_inner)

    total_numbers = len(data.index)
    avgvel = data.vel.mean()
    ic(total_numbers, avgvel)

    return data, avgvel


if __name__ == "__main__":
    average_inner("./tpwt.26.360", "station.lst")

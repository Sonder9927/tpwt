from pathlib import Path
from typing import Tuple

import numpy as np


def make_gridnode(region, dgrids: Tuple[float, float], outfile: Path):
    """
    create inversion grid nodes
    """
    DEG_TO_RAD = np.pi / 180
    EARTH_RADIUS_KM = 6371.0
    KM_PER_DEGREE = EARTH_RADIUS_KM * DEG_TO_RAD

    dlon, dlat = dgrids
    lonmax = region.east + 2
    lonmin = region.west - 2
    latmax = region.north + 2
    latmin = region.south - 2

    lons = np.arange(lonmin, lonmax + dlon / 2, dlon)
    lats = np.arange(latmin, latmax + dlat / 2, dlat)
    nlon = len(lons)
    nlat = len(lats)
    ngrid = nlon * nlat

    dy = KM_PER_DEGREE * dlat

    lon_grid, lat_grid = np.meshgrid(lons, lats, indexing="xy")
    dx_grid = KM_PER_DEGREE * np.cos(lat_grid * DEG_TO_RAD) * dlon

    grid_data = np.column_stack([
        lat_grid.ravel(order="F"),
        lon_grid.ravel(order="F"),
        dx_grid.ravel(order="F"),
        np.full(ngrid, dy),
    ])

    corner_lons = [lonmin + 2 * dlon, lonmax - 2 * dlon]
    corner_lats = [latmax - 2 * dlat, latmin + 2 * dlat]
    corners = [(lat, lon) for lon in corner_lons for lat in corner_lats]

    with outfile.open("w+") as f:
        f.write(f"grid{nlat:2}x{nlon:3}\n")
        f.write(f"{ngrid:6}\n")
        np.savetxt(f, grid_data, fmt="%8.2f%8.2f%8.3f%8.3f", delimiter="")

        for lat, lon in corners:
            f.write(f"{lat:8.2f}{lon:8.2f}\n")

        f.write(f"{nlon:3}")


def _make_gridnode(region, dgrid: list[float], outfile: Path):
    """
    create inversion grid nodes
    """
    convdeg = np.pi / 180
    circ = convdeg * 6371

    lonmax = region.east + 2
    lonmin = region.west - 2
    latmax = region.north + 2
    latmin = region.south - 2
    [dlon, dlat] = dgrid

    nlat = int((latmax - latmin) / dlat) + 1
    nlon = int((lonmax - lonmin) / dlon) + 1
    ngrid = nlat * nlon

    with outfile.open("w+") as f:
        f.write(f"grid{nlat:3}x{nlon:3}\n")
        f.write(f"{ngrid:6}\n")
        for ilon in range(nlon):
            for ilat in range(nlat):
                rlat = ilat * dlat + latmin
                rlon = ilon * dlon + lonmin

                dy = circ * dlat
                dx = circ * np.cos(rlat * convdeg) * dlon

                content = f"{rlat:8.2f}{rlon:8.2f}{dx:8.3f}{dy:8.3f}\n"
                f.write(content)

        for j in [lonmin + 2 * dlon, lonmax - 2 * dlon]:
            for i in [latmax - 2 * dlat, latmin + 2 * dlat]:
                f.write(f"{i:8.2f}{j:8.2f}\n")

        f.write(f"{nlon:3}")


def _inversion_nodes_TPWT(out_file: str, region, dgrid=None):
    """
    create inversion grid nodes
    """
    if dgrid is None:
        dgrid = [0.5, 0.5]
    convdeg = np.pi / 180
    circ = convdeg * 6371

    lonmax = region.east + 2
    lonmin = region.west - 2
    latmax = region.north + 2
    latmin = region.south - 2
    [dlon, dlat] = dgrid

    nlat = int((latmax - latmin) / dlat) + 1
    nlon = int((lonmax - lonmin) / dlon) + 1
    ngrid = nlat * nlon

    with open(out_file, "w+") as f:
        f.write("grid{:3}x{:3}\n".format(nlat, nlon))
        f.write("{:6}\n".format(ngrid))
        for ilon in range(nlon):
            for ilat in range(nlat):
                rlat = ilat * dlat + latmin
                rlon = ilon * dlon + lonmin

                dy = circ * dlat
                dx = circ * np.cos(rlat * convdeg) * dlon

                content = "{:8.2f}{:8.2f}{:8.3f}{:8.3f}\n".format(rlat, rlon, dx, dy)
                f.write(content)

        for j in [lonmin + 2 * dlon, lonmax - 2 * dlon]:
            for i in [latmax - 2 * dlat, latmin + 2 * dlat]:
                f.write("{:8.2f}{:8.2f}\n".format(i, j))

        f.write(f"{nlon:3}")

import numpy as np
from pathlib import Path


def make_gridnode(region, dgrid: list[float], outfile: Path):
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


def inversion_nodes_TPWT(out_file: str, region, dgrid=None):
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

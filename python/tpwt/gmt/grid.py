import pygmt


def grid_sample(data, region, spacing=0.5):
    # blockmean
    temp = pygmt.blockmean(data, region=region, spacing=0.5)
    # surface
    temp = pygmt.surface(data=temp, region=region, spacing=0.5)
    # grdsample
    temp = pygmt.grdsample(
        grid=temp,
        spacing=spacing,
    )
    data = pygmt.grd2xyz(temp)
    return data

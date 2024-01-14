from tpwt.rose import read_xyz


def average(f) -> float:
    """
    read the velocity and calculate the average value
    return avevel and title
    """
    ns = ["lo", "la", "vel"]
    df = read_xyz(f, ns)
    return df.vel.sum() / len(df)


###############################################################################
def dicts_of_per_vel(pers: list, vels: list) -> list[dict[str, float]]:
    if (lp := len(pers)) == len(vels):
        return [{"per": pers[n], "vel": vels[n]} for n in range(lp)]
    else:
        raise ValueError("#periods != #vels, please check parameters lists.")

import subprocess
from tpwt.utils.pather import binuse


def make_sta_dist_bin(evt_lst, sta_lst, sac_dir, outfile, binpath):
    """
    calc_distance to create sta_dist.lst
    """
    calc_distance_eq = binuse("calc_distance_earthquake", binpath=binpath)

    cmd_string = "echo shell start\n"
    cmd_string += f"{calc_distance_eq} {evt_lst} {sta_lst} {sac_dir}/ {outfile}\n"
    cmd_string += "echo shell end"

    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())


###############################################################################

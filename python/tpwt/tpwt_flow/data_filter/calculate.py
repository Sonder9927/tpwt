from concurrent.futures import ThreadPoolExecutor
import numpy as np
import shutil
import subprocess

from tpwt_p.rose import re_create_dir, get_binuse


def calculate_dispersion(evt, sta, outdir: str, disps: list):
    # cp disp model
    LOVE = "TPWT/utils/LOVE_400_100.disp"
    RAYL = "TPWT/utils/RAYL_320_80_32000_8000.disp"
    disps = disps or [LOVE, RAYL]
    cp_disps(disps, "./")

    # mk_pathfile makes file pathfile
    pathfile = "pathfile"
    mk_pathfile_TPWT(evt, sta, pathfile)

    # create tempinp using for GDM52_dispersion_TPWT
    tempinp = "tempinp"
    create_tempinp(pathfile, tempinp)

    # re-create directory 'path'
    re_create_dir(outdir)

    # calculate dispersion
    dispersion_out = "GDM52_dispersion.out"
    dispersion_TPWT = get_binuse("GDM52_dispersion_TPWT")
    gen_cor_pred_TPWT = get_binuse("gen_cor_pred_TPWT")

    cmd_string = "echo shell start\n"
    cmd_string += f"{dispersion_TPWT} < tempinp\n"
    cmd_string += f"{gen_cor_pred_TPWT} {dispersion_out} {outdir}\n"
    cmd_string += f"rm {pathfile} {tempinp} *.disp\n"
    cmd_string += "echo shell end"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

    shutil.move(dispersion_out, outdir)


###############################################################################


def cp_disps(disp_list: list[str], outdir: str):
    with ThreadPoolExecutor(max_workers=2) as pool:
        pool.map(shutil.copy, disp_list, [outdir] * len(disp_list))


def create_tempinp(pathfile, tempinp: str):
    with open(tempinp, "w+") as f:
        f.write("77\n")
        with open(pathfile, "r") as p:
            shutil.copyfileobj(p, f)
        f.write("99")


# mk_pathfile_TPWT
def mk_pathfile_TPWT(sta1, sta2, pathfile):
    """
    mk_pathfile makes file pathfile
    format: n1 n2 sta1 sta2 xlat1 xlon1 xlat2 xlon2
    """
    convdeg = np.pi / 180
    erad = 6371
    itemp = 6

    def d(la):
        return convdeg * (90 - la)

    f = open(pathfile, "w+")
    for i in range(len(sta1)):
        for j in range(len(sta2)):
            rad = np.cos(d(sta1.la[i])) * np.cos(d(sta2.la[j])) + np.sin(
                d(sta1.la[i])
            ) * np.sin(d(sta2.la[j])) * np.cos(convdeg * (sta1.lo[i] - sta2.lo[j]))

            dist = np.arccos(rad) * erad

            content = f"{itemp:>12}\n"
            content += f"{i+1:>5}{j+1:>5} "
            content += f"{sta1.sta[i]:<18} {sta2.sta[j]:<8}"
            content += f"{sta1.la[i]:10.4f}{sta1.lo[i]:10.4f}"
            content += f"{sta2.la[j]:10.4f}{sta2.lo[j]:10.4f}"
            content += f"{dist:12.2f}\n"

            f.write(content)

    f.close()

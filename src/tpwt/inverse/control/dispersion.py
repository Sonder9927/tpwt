import shutil
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd

from tpwt._core import make_cor_pred_files, make_pathfile
from tpwt.utils.pather import binuse

LOVE = "TPWT/utils/LOVE_400_100.disp"
RAYL = "TPWT/utils/RAYL_320_80_32000_8000.disp"


def calculate_dispersion(
    evt_csv: str,
    sta_csv: str,
    path_dir: Path,
    binpath: Path = Path("TPWT/bin"),
    disps: list[str] = [LOVE, RAYL],
):
    if path_dir.exists():
        print(f"{path_dir} exists, skip calculate dispersion.")
        return
    path_dir.mkdir(parents=True)

    pathfile = "outputs/pathfile"
    make_pathfile(evt_csv, sta_csv, pathfile)
    # create tempinp using for GDM52_dispersion_TPWT
    tempinp = "outputs/tempinp"
    create_tempinp(pathfile, tempinp)

    # cp disp model
    for disp in disps:
        shutil.copy(disp, "./")
    # calculate dispersion
    dispersion_out = "GDM52_dispersion.out"
    dispersion_TPWT = binuse("GDM52_dispersion_TPWT", binpath=binpath)
    # gen_cor_pred_TPWT = binuse("gen_cor_pred_TPWT", binpath=binpath)

    cmd_string = "echo shell start\n"
    cmd_string += f"{dispersion_TPWT} < {tempinp}\n"
    # cmd_string += f"{gen_cor_pred_TPWT} {dispersion_out} {path_dir}\n"
    cmd_string += f"rm {tempinp} *.disp\n"
    cmd_string += "echo shell end"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

    make_cor_pred_files(dispersion_out, str(path_dir))
    shutil.move(dispersion_out, path_dir)


###############################################################################


def create_tempinp(pathfile: str, tempinp: str):
    with open(tempinp, "w+") as f:
        f.write("77\n")
        with open(pathfile, "r") as p:
            shutil.copyfileobj(p, f)
        f.write("\n99")


def _make_pathfile(evt_df: pd.DataFrame, sta_df: pd.DataFrame) -> str:
    """
    mk_pathfile makes file pathfile
    format: n1 n2 evt sta xlat1 xlon1 xlat2 xlon2
    """
    pathfile = "pathfile"
    convdeg = np.pi / 180
    erad = 6371
    itemp = 6

    def d(la):
        return convdeg * (90 - la)

    contents = []
    for i in range(len(evt_df)):
        for j in range(len(sta_df)):
            la1 = evt_df.latitude[i]
            la2 = sta_df.latitude[j]
            lo1 = evt_df.longitude[i]
            lo2 = sta_df.longitude[j]
            rad = np.cos(d(la1)) * np.cos(d(la2)) + np.sin(d(la1)) * np.sin(
                d(la2)
            ) * np.cos(convdeg * (lo1 - lo2))

            dist = np.arccos(rad) * erad

            content = f"{itemp:>12}\n"
            content += f"{i + 1:>5}{j + 1:>5} "
            content += f"{evt_df.time[i]:<18} {sta_df.station[j]:<8}"
            content += f"{la1:10.4f}{lo1:10.4f}"
            content += f"{la2:10.4f}{lo2:10.4f}"
            content += f"{dist:12.2f}\n"
            contents.append(content)

    with open(pathfile, "w+") as f:
        f.writelines(contents)

    return pathfile

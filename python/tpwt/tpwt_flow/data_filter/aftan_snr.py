from concurrent.futures import ProcessPoolExecutor
import os
from pathlib import Path
import subprocess

from icecream import ic
from tpwt_p.rose import get_binuse, glob_patterns


def process_events_aftan_snr(sac_dir: str, path: str):
    """
    aftan and SNR in sac/event/
    and
    output is target/path/
    """
    work = Path(".").cwd()
    dir_ref = work / path
    # filelist = 'filelist'

    # spectral_snr_TPWT
    spectral_snr_TPWT = get_binuse("spectral_snr_TPWT", bin_from=work)

    events = glob_patterns("glob", Path(sac_dir), ["20*/"])
    # aftani_c_pgl_TPWT
    aftani_c_pgl_TPWT = get_binuse("aftani_c_pgl_TPWT", bin_from=work)

    with ProcessPoolExecutor(max_workers=4) as executor:
        for e in events:
            executor.submit(
                process_event_aftan_and_SNR,
                e,
                dir_ref,
                work,
                spectral_snr_TPWT,
                aftani_c_pgl_TPWT,
            )


###############################################################################


def process_event_aftan_and_SNR(
    event, dir_ref, work, spectral_snr_TPWT, aftani_c_pgl_TPWT
):
    """
    batch function for process_events_flag_aftan_and_SNR
    """
    sacs = glob_patterns("glob", event, ["*.sac"])

    filelist = "filelist"

    # go into sac data directory
    os.chdir(str(event))

    with open(filelist, "w+") as f:
        for sac in sacs:
            sf = sac.name
            # filelist
            f.write(sf + "\n")
            # aftan
            aftani_c_pgl_TPWT_run(dir_ref, sf, aftani_c_pgl_TPWT)

    cmd_string = f"{spectral_snr_TPWT} {filelist} > temp.dat \n"
    cmd_string += "rm temp.dat"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

    ic(event.name, "done.")
    os.chdir(str(work))


def aftani_c_pgl_TPWT_run(dir_ref: Path, sac_file: str, aftani_c_pgl_TPWT):
    content = f"0 2.5 5.0 10 250 20 1 0.5 0.2 2 {sac_file}"
    param_dat = "param.dat"
    with open(param_dat, "w") as p:
        p.write(content)

    sac_parts = sac_file.split(".")
    ref = dir_ref / "{0[0]}_{0[1]}.PH_PRED".format(sac_parts)

    cmd_string = f"{aftani_c_pgl_TPWT} {param_dat} {ref}\n"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

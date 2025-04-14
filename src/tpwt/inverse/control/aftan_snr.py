import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm

from tpwt.utils.pather import binuse


def aftan_snr(sac_dir: Path, path_dir: Path, binpath: Path):
    """
    aftan and SNR in sac/event/
    """
    work_dir = Path(".").cwd()
    path_dir_obs = work_dir / path_dir

    # spectral_snr_TPWT
    spectral_snr_TPWT = binuse("spectral_snr_TPWT", binpath=binpath)

    events = [i for i in sac_dir.iterdir() if i.is_dir()]
    # aftani_c_pgl_TPWT
    aftani_c_pgl_TPWT = binuse("aftani_c_pgl_TPWT", binpath=binpath)

    with ProcessPoolExecutor(max_workers=4) as executor:
        futures = {
            executor.submit(
                process_aftan_snr_per_event,
                event,
                work_dir,
                path_dir_obs,
                aftani_c_pgl_TPWT,
                spectral_snr_TPWT,
            )
            for event in events
        }
        with tqdm(total=len(events)) as pbar:
            for future in as_completed(futures):
                future.result()
                pbar.update(1)


###############################################################################


def process_aftan_snr_per_event(
    event_dir, work_dir, path_dir, aftani_c_pgl_TPWT, spectral_snr_TPWT
) -> str:
    """
    batch function for aftan_snr
    """
    os.chdir(str(event_dir))

    filelist = "filelist"
    # aftan
    _aftan(event_dir, path_dir, filelist, aftani_c_pgl_TPWT)
    # snr
    _snr(filelist, spectral_snr_TPWT)

    os.chdir(str(work_dir))
    return f"Finish event: {event_dir}"


def _snr(filelist, spectral_snr_TPWT):
    cmd_string = f"{spectral_snr_TPWT} {filelist} > temp.dat \n"
    cmd_string += "rm temp.dat"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())


def _aftan(event_dir, path_dir, filelist, aftani_c_pgl_TPWT):
    contents = []
    for sac in event_dir.glob("*.LHZ.sac"):
        sacfn = sac.name
        contents.append(sacfn + "\n")
        # aftan
        _aftan_per_sac(path_dir, sacfn, aftani_c_pgl_TPWT)

    # filelist
    with open(filelist, "w+") as f:
        f.writelines(contents)


def _aftan_per_sac(path_dir: Path, sac_file: str, aftani_c_pgl_TPWT):
    content = f"0 2.5 5.0 10 250 20 1 0.5 0.2 2 {sac_file}"
    param_dat = "param.dat"
    with open(param_dat, "w") as p:
        p.write(content)

    sac_parts = sac_file.split(".")
    ref = path_dir / "{0[0]}_{0[1]}.PH_PRED".format(sac_parts)

    cmd_string = f"{aftani_c_pgl_TPWT} {param_dat} {ref}\n"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

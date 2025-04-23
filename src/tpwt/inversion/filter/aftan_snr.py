import os
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from tqdm import tqdm


def aftan_snr(sac_dir: Path, path_dir: Path, aftani_c_pgl_TPWT, spectral_snr_TPWT):
    """
    aftan and SNR in sac/event/

    Parameters:
        sac_dir: sac data
        path_dir: the dir where puts PH_PRED files
        binpath: bin dir
    """
    work_dir = Path().cwd()
    path_dir_obs = work_dir / path_dir

    events = [work_dir / i for i in sac_dir.iterdir() if i.is_dir()]

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
                result = future.result()
                pbar.update(1)
                pbar.set_postfix(stats=result)


###############################################################################


def process_aftan_snr_per_event(
    event_dir: Path, work_dir, path_dir, aftani_c_pgl_TPWT, spectral_snr_TPWT
) -> str:
    """
    batch function for aftan_snr
    """
    os.chdir(str(event_dir))

    filelist = "filelist"
    # aftan -> disp files
    _aftan(event_dir, path_dir, filelist, aftani_c_pgl_TPWT)
    # snr -> snr file
    _snr(filelist, spectral_snr_TPWT)

    os.chdir(str(work_dir))
    return f"Finish: {event_dir.name}"


def _snr(filelist, spectral_snr_TPWT):
    out_msg = "temp.dat"
    cmd_string = f"{spectral_snr_TPWT} {filelist} > {out_msg} \n"
    cmd_string += f"rm {out_msg} \n"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())


def _aftan(event_dir, path_dir, filelist, aftani_c_pgl_TPWT):
    saclst = []
    param_dat = "param.dat"
    params = "0 2.5 5.0 10 250 20 1 0.5 0.2 2"

    cmd_str = "shell start aftan"
    for sac in event_dir.glob("*.sac"):
        sacfn = sac.name
        parts = sacfn.split(".")
        ref = path_dir / f"{parts[0]}_{parts[1]}.PH_PRED"

        cmd_str += f'echo "{params} {sacfn}" > {param_dat} \n'
        cmd_str += f"{aftani_c_pgl_TPWT} {param_dat} {ref} \n"
        saclst.append(sacfn + "\n")
    cmd_str += f"rm {param_dat}\n"

    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_str.encode())

    # filelist
    with open(filelist, "w+") as f:
        f.writelines(saclst)

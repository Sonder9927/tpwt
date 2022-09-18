from icecream import ic
from multiprocessing import Process
from threading import Thread
import pandas as pd
import os, pathlib, shutil
import subprocess

# My scripts
# functions
from pysrc.get_param import get_param_json
from pysrc.tpwt import (
    get_binuse,
    mk_pathfile_TPWT,
    f_generator,
)

"""
01
"""

def get_STA_v2(file_name: str):
    """
    turn type as station, lo, la, vel... to station, NR, la, lo
    """
    sta = pd.read_csv(
        file_name,
        sep = '\s+',
        usecols = [0, 1, 2],
        names = ['sta', 'la', 'lo'],
        engine = 'python'
    )
    sta[['la', 'lo']] = sta[['lo', 'la']]

    return sta


def cp_rayl_love(rayl_disp, love_disp, outdir):
    t1 = Thread(target=shutil.copy, args=[rayl_disp, outdir])
    t1.start()
    t2 = Thread(target=shutil.copy, args=[love_disp, outdir])
    t2.start()

    t1.join()
    t2.join()
    ic('copy disp model completed')


# GDM52_dispersion_TPWT
def calculate_GDM52_dispersion(evt, sta, outdir):
    # cp disp model
    LOVE = "TPWT/utils/LOVE.disp"
    RAYL = "TPWT/utils/RAYL.disp"
    cp_rayl_love(RAYL, LOVE, './')

    # mk_pathfile makes file pathfile
    pathfile = 'pathfile'
    mk_pathfile_TPWT(evt, sta, pathfile)

    # create tempinp using for GDM52_dispersion_TPWT
    def create_tempinp(pathfile, tempinp: str):
        with open(tempinp, "w+") as f:
            f.write("77\n")
            with open(pathfile, "r") as p:
                shutil.copyfileobj(p, f)
            f.write("99")

    tempinp = 'tempinp'
    create_tempinp(pathfile, tempinp)

    # re-create directory 'path'
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)

    # calculate dispersion
    dispersion_out = "GDM52_dispersion.out"
    dispersion_TPWT = get_binuse('GDM52_dispersion_TPWT')
    gen_cor_pred_TPWT = get_binuse('gen_cor_pred_TPWT')

    cmd_string = 'echo shell start\n'
    cmd_string += f'{dispersion_TPWT} < tempinp\n'
    cmd_string += f'{gen_cor_pred_TPWT} {dispersion_out} {outdir}\n'
    cmd_string += f'rm {pathfile} {tempinp} *.disp\n'
    cmd_string += 'echo shell end'
    subprocess.Popen(
        ['bash'],
        stdin = subprocess.PIPE
    ).communicate(cmd_string.encode())
    shutil.move(dispersion_out, outdir)

    ic('Calculate GDM52 dispersion finished.')


def flag_GDM52_run(evt_file, sta_file, path='path'):
    # get sta_v2
    evt_sta = get_STA_v2(evt_file)
    sta_sta = get_STA_v2(sta_file)

    # genetate inter-station dispersion curves using the GDM model.
    calculate_GDM52_dispersion(evt_sta, sta_sta, path)

    # mark finish
    pathlib.Path('flag_GDM52').touch()
    ic("Flag GDM52 done.")

##############################################################################

def aftani_c_pgl_TPWT_run(dir_ref, sac_file):
    content = "0 2.5 5.0 10 250 20 1 0.5 0.2 2 "  # zui hou you ge kong ge...
    content += sac_file
    param_dat = 'param.dat'
    with open(param_dat, 'w') as p:
        p.write(content)

    sac_parts = sac_file.split('.')
    ref = dir_ref / '{0[0]}_{0[1]}.PH_PRED'.format(sac_parts)

    # spectral_snr_TPWT
    aftani_c_pgl_TPWT = get_binuse('aftani_c_pgl_TPWT', bin_from=work)

    cmd_string = f'{aftani_c_pgl_TPWT} {param_dat} {ref}\n'
    subprocess.Popen(
        ['bash'],
        stdin = subprocess.PIPE
    ).communicate(cmd_string.encode())


def flag_aftan_and_SNR_run(dir_ref, filelist):
    """
    flag_aftan <- aftani_c_pgl_TPWT
    flag_SNR <- spectral_snr_TPWT
    """
    sac_file = f_generator('.sac')
    with open(filelist, 'w+') as f:
        stat = True
        while stat:
            try:
                # get sac file name
                sf = next(sac_file)
                # filelist
                f.write(sf + '\n')
                # aftan
                aftani_c_pgl_TPWT_run(dir_ref, sf)
            except StopIteration:
                stat = False

    # spectral_snr_TPWT
    spectral_snr_TPWT = get_binuse('spectral_snr_TPWT', bin_from=work)

    cmd_string = f'{spectral_snr_TPWT} {filelist} > temp.dat \n'
    subprocess.Popen(
        ['bash'],
        stdin = subprocess.PIPE
    ).communicate(cmd_string.encode())

    # mark finish
    pathlib.Path('flag_aftan_and_SNR').touch()
    ic("Flag aftan and SNR done.")


def process_event_flag_aftan_and_SNR(event, dir_ref, filelist):
    """
    go into event
    process it if flag_aftan_and_SNR doesn't exist.
    """
    os.chdir(event)

    if os.path.exists('flag_aftan_SNR'):
        ic('flag_SNR existed, will skip running this part.')
        ic(event, "skipped")
    else:
        flag_aftan_and_SNR_run(dir_ref, filelist)
        ic(event, "finished")


def process_events_flag_aftan_and_SNR_run(sac='SAC', path='path'):
    """
    touch flag_aftan and flag_SNR in sac/event/
    and
    output is ./path/
    """
    # global work directory
    global work
    work = pathlib.Path.cwd()
    dir_ref = work / path
    filelist = 'filelist'

    # go into sac data directory
    os.chdir(sac)
    events = os.listdir()
    process_list = []
    for event in events:
        if os.path.isdir(event):
            p = Process(target=process_event_flag_aftan_and_SNR,
                       args=[event, dir_ref, filelist])
            process_list.append(p)
            p.start()

    for p in process_list:
        p.join()

    # go back to work directory
    os.chdir(work)
    ic("flag_aftan and flag_SNR are created.")

def tpwt_01(param_json):
    # get parameters
    param = get_param_json(param_json)
    # files
    p_f = param['files']
    evt = p_f["evt"]
    sta = p_f["sta"]
    path_dir = p_f['path']
    sac = p_f['sac']

    # flag_GDM52
    if os.path.exists('flag_GDM52'):
        ic('flag_GDM52 existed, will skip running this part.')
    else:
        if (os.path.exists(sta)
            and os.path.exists(evt)):
            flag_GDM52_run(evt, sta, path_dir)
        else:
            raise Exception('No station.lst or event.lst found.')

    # flag_aftan and flag_SNR
    process_events_flag_aftan_and_SNR_run(sac, path_dir)
    
    ic("TPWT step 1 done")


if __name__ == "__main__":
    tpwt_01("param.json")

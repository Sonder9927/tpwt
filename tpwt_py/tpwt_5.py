from icecream import ic
from multiprocessing import Process
import os, pathlib, shutil
import subprocess

# My scripts
# functions
from pysrc.get_param import get_param_json
from pysrc.tpwt import (
    get_binuse,
    simanner_TPWT_run,
    sensitivity_TPWT,
    get_TPWT_output_dir,
    rdsetupsimul_phamp_from_earthquake_TPWT,
    simanner160_and_gridgenvar,
)

# classes
from pysrc.get_param import Param

"""
05
"""


def process_in_per_dir(per, smooth, damp, out_dir):
    """
    process data generated from step 4
    in TPWT_param/per
    """
    if os.path.exists(eq := f'eqlistper{per}'):
        if os.path.exists(out_dir):
            shutil.rmtree(out_dir)
        os.mkdir(out_dir)
    else:
        err_des = f'No {eq} found!'
        err_des += 'Please make sure tpwt 4 is correctly finished.'
        raise Exception(err_des)

    # simannerr100
    simanner_TPWT_run(100, eq, bin_from=work)

    # return avgvel and std
    vel_f = f"velarea.{per}.1.{smooth}.{damp}.sa100kern"
    with open(vel_f, 'r') as f:
        velarea = f.readline()
    
    return velarea.split()[1]


def process_to_new_2d_of_per_dir(p):
    # find bad kern100
    # will create eqlistper.fine
    find_bad_kern100 = get_binuse("find_bad_kern100", bin_from=work)
    c_string = f'{find_bad_kern100} '
    c_string += f'{p.ampcut} {p.tcut} {p.stacut} eqlistper{p.period}'
    subprocess.Popen(
        ['bash'],
        stdin = subprocess.PIPE
    ).communicate(c_string.encode())

    # get linenum of eqlistper.fine
    eq_fine = r'eqlistper.fine'
    with open(eq_fine, 'r') as f1:
        content_list = f1.readlines()
    # update eqlistper{per}
    with open(f'{p.output}/eqlistper{p.period}.update', 'w+') as f2:
        for c in content_list[:-14]:
            f2.write(c)

    move_list = [eq_fine, 'stationid.dat', 'invrsnodes']
    for mf in move_list:
        shutil.move(mf, p.output)


def process_in_new_2d_of_per_dir(p, wave_type):
    sensitivity_TPWT(p, wave_type, bin_from=work)

    # do rdsetupsimul phamp again
    per = p.period
    eqlistper = f'eqlistper{per}.update'
    sens_dat = f"sens{per}s{p.smooth}km.dat"
    sec_snr_dis = work / p.all_events / f"{per}sec_{p.snr}snr_{p.dist}dis"
    rdsetupsimul_phamp_from_earthquake_TPWT(p, eqlistper, sens_dat, sec_snr_dis, bin_from=work)

    rm_list = [
        eqlistper,
        f'resmax{per}.dat',
        f'eqlistper.fine',
        f'phampcor.v3.{per}',
    ]
    for rf in rm_list:
        os.remove(rf)

    eqlistper = f'eqlistper{per}'
    shutil.move(f'eqlistper.v3.{per}', eqlistper)

    # simannerr160 and create grid file
    simanner160_and_gridgenvar(p, eqlistper, bin_from=work)


def process_period_grid(param, out_TPWT, wave_type):
    per = str(param.period)
    per_dir = out_TPWT / per

    # go into TPWT_param/per
    # will mkdir output to put result grid data in
    os.chdir(per_dir)
    param.vel = process_in_per_dir(per, param.smooth, param.damp, param.output)

    process_to_new_2d_of_per_dir(param)

    # go into output directory, default is new_2d
    os.chdir(param.output)
    process_in_new_2d_of_per_dir(param, wave_type)


    ic("period", param.period, "done")


def process_periods_grid(param, per_list):
    # check if dir 'TPWT_param' exists
    # get TPWT output dir
    out_TPWT = get_TPWT_output_dir(param.snr, param.tcut, param.smooth, param.damping)
    out_TPWT = pathlib.Path(out_TPWT)
    if not os.path.exists(out_TPWT):
        err_description = f'No {out_TPWT} found.'
        err_description += 'Please make sure tpwt step 4 is done.'
        raise Exception(err_description)

    # wave type: rayleigh or love
    # (this version only support rayleigh)
    wave_type = ['rayleigh', 'love']
    # process every period
    process_list = []
    for per in per_list:
        param.period = per
        p = Process(target=process_period_grid,
                   args=[param, out_TPWT, wave_type[0]])
        process_list.append(p)
        p.start()

    for p in process_list:
        p.join()

    # mark finish
    pathlib.Path('flag_grid').touch()
    ic("Result grid created and flag grid.")
    ic("All steps done.")


def tpwt_05(param_json, *, snr=None, tcut=None, smooth=None, damping=None):
    global work
    work = pathlib.Path.cwd()

    # instancs a parameters class
    p5 = Param
    # get parameters
    param = get_param_json(param_json)
    # variables
    p_var = param['variables']
    p5.snr = snr or p_var['snr'][0]
    p5.tcut = tcut or p_var['tcutoff'][0]
    p5.smooth = smooth or p_var['smooth'][0]
    p5.damping = damping or p_var['damping'][0]
    p5.damp = str(p5.damping).split('.')[1]
    # files
    p_f = param['files']
    p5.all_events = p_f['all_events']
    p5.output = p_f['output']
    # immutables
    p_immu = param['immutables']
    p5.dist = p_immu['dist']
    p5.nsta = p_immu['nsta_cutoff']
    p5.region = p_immu['region']
    p5.stacut = p_immu['stacut_per']
    p5.ampcut = p_immu['ampcut']
    p5.ampevtrmscut = p_immu['ampevtrmscut']

    # flag_sta_dist
    if os.path.exists('flag_grid'):
        ic('The flag_grid existed, will skip running this part.')
    else:
        # process_periods_grid(p5, p_immu['period'])
        process_periods_grid(p5, [p_immu['period'][2]])
    
    ic("TPWT step 5 done")


if __name__ == "__main__":
    tpwt_05("param.json", snr=15, tcut=10, smooth=65, damping=.25)

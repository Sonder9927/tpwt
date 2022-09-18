"""


Not Complete Yet.


"""
from icecream import ic
from multiprocessing import Process
import os, pathlib, shutil
import subprocess
import linecache

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
06 -- checkboard
"""


def process_in_result_dir(p):
    """
    process data generated from tpwt
    in TPWT_param/per/new_2d
    """
    # create check directory
    if os.path.exists(ck := p.check_dir):
        shutil.rmtree(ck)
    os.mkdir(ck)

    # get avgvel
    lines = linecache.getlines(f'eqlistper{p.period}')
    avgvel = lines[-3]
    ic(float(avgvel))


def process_period_grid(param):
    # check if dir 'TPWT_param/per/new_2d' exists
    # get TPWT output dir
    out_TPWT = get_TPWT_output_dir(param.snr, param.tcut, param.smooth, param.damping)
    out_TPWT = pathlib.Path(out_TPWT)
    per = str(param.period)
    res_dir = out_TPWT / per / param.output
    # go into new_2d if it exists
    if os.path.exists(res_dir):
        os.chdir(res_dir)
    else:
        err_description = f'No {res_dir} found.'
        err_description += 'Please make sure both tpwt 4 and 5 are done.'
        raise Exception(err_description)

    # re-create check dir if it exists already
    process_in_result_dir(param)


def process_periods_check_board(param, per_list):
    global work
    work = pathlib.Path.cwd()

    # check dir and file name
    param.check_dir = f'check_{param.dcheck}X{param.dcheck}_{param.dvel}%'
    param.check_file = f'{param.check_dir}.dat'
    # wave type: rayleigh or love
    # (this version only support rayleigh)
    wave_type = ['rayleigh', 'love']
    # process every period
    process_list = []
    for per in per_list:
        param.period = per
        p = Process(target=process_period_grid,
                   args=[param])
        process_list.append(p)
        p.start()

    for p in process_list:
        p.join()


def tpwt_06(param_json, *, snr=None, tcut=None, smooth=None, damping=None, dcheck=None, dvel=None):
    # instancs a parameters class
    p6 = Param
    # get parameters
    param = get_param_json(param_json)
    # variables
    p_var = param['variables']
    p6.snr = snr or p_var['snr'][0]
    p6.tcut = tcut or p_var['tcutoff'][0]
    p6.smooth = smooth or p_var['smooth'][0]
    p6.damping = damping or p_var['damping'][0]
    p6.damp = str(p6.damping).split('.')[1]
    p6.dcheck = dcheck or p_var['dcheck'][0]
    p6.dvel = dcheck or p_var['dvel'][0]
    # files
    p_f = param['files']
    p6.output = p_f['output']
    # immutables
    p_immu = param['immutables']
    p6.dist = p_immu['dist']
    p6.nsta = p_immu['nsta_cutoff']
    p6.region = p_immu['region']
    p6.stacut = p_immu['stacut_per']
    p6.ampcut = p_immu['ampcut']
    p6.ampevtrmscut = p_immu['ampevtrmscut']
    p6.channel = p_immu['channel']

    # flag_sta_dist
    if os.path.exists('flag_check'):
        ic('The flag_check existed, will skip running this part.')
    else:
        # process_periods_grid(p6, p_immu['period'])
        process_periods_check_board(p6, [p_immu['period'][2]])
    


if __name__ == "__main__":
    tpwt_06("param.json", snr=15, tcut=10, smooth=65, damping=.25, dcheck=1, dvel=8)

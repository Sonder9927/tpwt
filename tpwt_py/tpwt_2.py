from icecream import ic
from multiprocessing import Process
import os, pathlib, shutil
import subprocess

# My scripts
# functions
from pysrc.get_param import get_param_json
from pysrc.tpwt import (
    get_binuse,
    plot_phase_time,
    plot_amp,
)

# classes
from pysrc.get_param import Param

"""
02
"""

def flag_sta_dist_run(p):
    calc_distance_eq = get_binuse('calc_distance_earthquake')
    find_phvel_amp_eq = get_binuse('find_phvel_amp_earthquake')

    cmd_string = 'echo shell start\n'
    cmd_string += f'{calc_distance_eq} {p.evt} {p.sta} {p.sac}/\n'
    cmd_string += f'{find_phvel_amp_eq} '
    cmd_string += f'{p.period} sta_dist.lst {p.snr} {p.dist} {p.sac}/\n'
    cmd_string += f'mv {p.period}sec_{p.snr}snr_{p.dist}dis {p.all_events}/\n'
    cmd_string += 'echo shell end'
    subprocess.Popen(
        ['bash'],
        stdin = subprocess.PIPE
    ).communicate(cmd_string.encode())


##############################################################################


def plot_event_phase_time_and_amp(p, event):
    """
    plot phase time
    plot amp
    """
    stanum = len(open(event, 'r').readlines())

    if stanum >= p.nsta:
        correct_tt_select_data = get_binuse('correct_tt_select_data', bin_from=work)

        cmd_string = 'echo shell start\n'
        cmd_string += f'{correct_tt_select_data} '
        cmd_string += f'{event} {p.period} {p.nsta} {p.stacut} '
        cmd_string += f'{p.c_lo} {p.c_la} {p.tcut}\n'
        cmd_string += 'echo shell end'
        subprocess.Popen(
            ['bash'],
            stdin = subprocess.PIPE
        ).communicate(cmd_string.encode())

        plot_phase_time(event, p.region)
        plot_amp(event, p.region)
        if os.path.exists(event + '_v1'):
            plot_phase_time(event+'_v1', p.region)
            plot_amp(event+'_v1', p.region)
        

def plot_events_phase_time_and_amp(param):
    global work
    work = pathlib.Path.cwd()
    os.chdir(
        f'{param.all_events}/{param.period}sec_{param.snr}snr_{param.dist}dis'
    )
    events = [i for i in os.listdir() if i.endswith('ph.txt')]
    # process every event
    # cannot use Thread
    process_list = []
    for event in events:
        p = Process(target=plot_event_phase_time_and_amp,
                   args=[param, event])
        process_list.append(p)
        p.start()

    for p in process_list:
        p.join()
    
    os.chdir(work)


def process_period_sta_dist(param):

    flag_sta_dist_run(param)

    plot_events_phase_time_and_amp(param)

    ic("period", param.period, "done")


def process_periods_sta_dist(param, periods=[26,]):
    # make directory
    # re-create directory 'all_events'
    outdir = param.all_events
    if os.path.exists(outdir):
        shutil.rmtree(outdir)
    os.mkdir(outdir)

    # process every period
    process_list = []
    for per in periods:
        param.period = per
        p = Process(target=process_period_sta_dist,
                   args=[param,])
        process_list.append(p)
        p.start()

    for p in process_list:
        p.join()

    # mark finish
    shutil.move('sta_dist.lst', 'flag_sta_dist')
    ic("Flag station distance done.")


def tpwt_02(param_json, *, snr=None, tcut=None):
    # instancs a parameters class
    p2 = Param
    # get parameters
    param = get_param_json(param_json)
    # variables
    p_var = param['variables']
    p2.snr = snr or p_var['snr'][0]
    p2.tcut = tcut or p_var['tcutoff'][0]
    # files
    p_f = param['files']
    p2.evt = p_f["evt"]
    p2.sta = p_f["sta"]
    p2.sac = p_f['sac']
    p2.all_events = p_f['all_events']
    # immutables
    p_immu = param['immutables']
    p2.dist = p_immu['dist']
    p2.nsta = p_immu['nsta_cutoff']
    p2.stacut = p_immu['stacut_per']
    p2.region = p_immu['region']
    ic(p2.region)
    p2.c_lo = 15
    p2.c_la = 15
    ic(p2.c_lo, p2.c_la)

    # flag_sta_dist
    if os.path.exists('flag_sta_dist'):
        ic('The flag_sta_dist existed, will skip running this part.')
    else:
        if (os.path.exists(p2.sta)
            and os.path.exists(p2.evt)):
            # process_periods_sta_dist(p2, p_immu['period'])
            process_periods_sta_dist(p2)
        else:
            raise Exception('No station.lst or event.lst found.')
    
    ic("TPWT step 2 done")


if __name__ == "__main__":
    tpwt_02("param.json", snr=15, tcut=10)

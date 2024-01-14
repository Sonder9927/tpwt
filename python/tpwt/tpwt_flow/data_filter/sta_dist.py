from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from pathlib import Path
import subprocess, shutil

from tpwt_p.rose import glob_patterns, get_binuse, get_dirname, re_create_dir
from tpwt_p.gmt import gmt_amp, gmt_phase_time


def process_periods_sta_dist(param):
    # re-create directory 'all_events'
    all_events = Path(param.target("all_events"))
    re_create_dir(all_events)

    # calc_distance to create sta_dist.lst
    evt = param.target("evt_lst")
    sta = param.target("sta_lst")
    sac = param.target("sac")
    sta_dist = r"target/sta_dist.lst"
    calculate_sta_dist(evt, sta, sac, sta_dist)

    find_phvel_amp_eq = get_binuse("find_phvel_amp_earthquake")
    correct_tt_select_data = get_binuse("correct_tt_select_data")

    periods = param.periods()
    with ProcessPoolExecutor(max_workers=4) as executor:
        for p in periods:
            executor.submit(
                process_period_sta_dist,
                param,
                p,
                sta_dist,
                find_phvel_amp_eq,
                correct_tt_select_data,
            )

    Path(sta_dist).unlink()

    # plot phase time and amp of all events
    events = glob_patterns("glob", all_events, ["**/*ph.txt"])
    region = param.region().original()
    with ProcessPoolExecutor(max_workers=4) as executor:
        for e in events:
            executor.submit(event_phase_time_and_amp, e, region)


###############################################################################


def calculate_sta_dist(evt, sta, sac, sta_dist):
    """
    calc_distance to create sta_dist.lst
    """
    calc_distance_eq = get_binuse("calc_distance_earthquake")

    cmd_string = "echo shell start\n"
    cmd_string += f"{calc_distance_eq} {evt} {sta} {sac}/ {sta_dist}\n"
    cmd_string += "echo shell end"

    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())


###############################################################################
"""
batch function
"""


# process every period
def process_period_sta_dist(
    p, period, sta_dist, find_phvel_amp_eq, correct_tt_select_data
):
    """
    batch function for process_periods_sta_dist
    """
    # bind period to bp
    calc_distance_find_eq(p, period, sta_dist, find_phvel_amp_eq)

    sec = Path(
        p.parameter("all_events")
        / get_dirname(
            "sec", period=period, snr=p.parameter("snr"), dist=p.parameter("dist")
        )
    )

    all_periods_sec(p, sec, period, correct_tt_select_data)


###############################################################################


def calc_distance_find_eq(p, period, sta_dist, find_phvel_amp_eq):
    snr = p.parameter("snr")
    dist = p.parameter("dist")
    sac = p.parameter("sac")
    cmd_string = "echo shell start\n"
    cmd_string += f"{find_phvel_amp_eq} "
    cmd_string += f"{period} {sta_dist} {snr} {dist} {sac}/\n"
    cmd_string += "echo shell end"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

    all_events = p.target("all_events")
    shutil.move(get_dirname("sec", period=period, snr=snr, dist=dist), all_events)


def all_periods_sec(param, sec, period, correct_tt_select_data):
    # ["*ph.txt", "*_v1"]
    events = glob_patterns("glob", sec, ["*ph.txt"])
    with ThreadPoolExecutor(max_workers=10) as executor:
        for e in events:
            executor.submit(ph_txt_v1, param, period, e, correct_tt_select_data)


# process every event
# cannot use Thread
def ph_txt_v1(p, period, event, correct_tt_select_data):
    """
    batch function
    plot phase time
    plot amp
    """
    stanum = len(open(event, "r").readlines())
    nsta = p.parameter("nsta")
    stacut = p.parameter("stacut_per")
    [ref_lo, ref_la] = p.ref_sta()
    tcut = p.parameter("tcut")

    if stanum >= nsta:
        cmd_string = "echo shell start\n"
        cmd_string += f"{correct_tt_select_data} "
        cmd_string += f"{event} {period} {nsta} {stacut} "
        cmd_string += f"{ref_lo} {ref_la} {tcut}\n"
        cmd_string += "echo shell end"
        subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(
            cmd_string.encode()
        )


###############################################################################


def event_phase_time_and_amp(event, region):
    """
    plot phase time and amp of all events with region
    """
    if event.stat().st_size != 0:
        gmt_phase_time(event, region)
        gmt_amp(event, region)

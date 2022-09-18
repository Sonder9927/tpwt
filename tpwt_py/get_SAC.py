# get_SAC.py
# author : Sonder Merak Winona
# created: 6th April 2022
# version: 1.3

'''
This script will move events directories having 14 numbers in cut_dir to sac_dir
and batch rename a group of sac files in given directory renamed with 12 numbers.

From 
XX.BDXXX.00.XXZ.X.2022001105112.sac
To
event.station.LHZ.sac

Then add information of both event and station to head of sac files in SAC directory
'''

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from icecream import ic
import pandas as pd
import os, shutil
import subprocess


def format_sac(target_old):
    """
    rename and ch sac files
    """
    evt_name = target_old.parent.name
    sta_name = target_old.name.split('.')[1]
    new_name = f"{evt_name}.{sta_name}.LHZ.sac"

    target_new = target_old.parent / new_name
    shutil.move(target_old, target_new)
    return target_new


def ch_sac(sac_path):
    """
    change head of sac file to generate dist information
    """
    # ch evla, evlo, evdp(optional) and stla, stlo, stel(optional)
    [evt_name, sta_name, channel, _] = sac_path.name.split('.')

    s = "wild echo off \n"
    s += "r {} \n".format(sac_path)
    s += f"ch evla {evt['la'][evt_name]}\n"
    s += f"ch evlo {evt['lo'][evt_name]}\n"
    # s += "ch evdp {}\n".format(evt['dp'][evt_name])
    s += f"ch stla {sta['la'][sta_name]}\n"
    s += f"ch stlo {sta['lo'][sta_name]}\n"
    # s += f"ch stel {sta['dp'][sta_name]}\n"
    s += f"ch kcmpnm {channel}\n"
    s += "wh \n"
    s += "q \n"

    os.putenv("SAC_DISPLAY_COPYRIGHT", "0")
    subprocess.Popen(['sac'], stdin=subprocess.PIPE).communicate(s.encode())


def batch_event(cut_evt):
    """
    batch function to process every event
    move events directories
    format sac files
    """
    # move
    sac_evt = sac / cut_evt.name[:12]
    shutil.copytree(cut_evt, sac_evt)

    # rename
    sacs = list(sac_evt.glob("*"))
    for sac_file in sacs:
        sac_path = format_sac(sac_file)
        ch_sac(sac_path)


def get_SAC(cut_dir, sac_dir, evt_lst, sta_lst):
    """
    rename events directories
    format sac files
    ch sac files
    """
    global sac, evt, sta

    if (os.path.exists(sta_lst) and os.path.exists(evt_lst)):
        ic("will create SAC")
    else:
        raise FileNotFoundError('No station.lst or event.lst found.')

    sta = pd.read_csv(sta_lst, delim_whitespace=True, names=["sta", "lo", "la"], index_col="sta")
    evt = pd.read_csv(evt_lst, delim_whitespace=True, names=["evt", "lo", "la"], dtype={"evt": str}, index_col="evt")
    sac = Path(sac_dir)
    # clear and re-create
    if sac.exists():
        shutil.rmtree(sac)
    sac.mkdir(parents=True)

    # get list of events directories
    cut_evts = list(Path(cut_dir).glob("*/**"))
    # batch process
    ic("batch processing...")
    with ThreadPoolExecutor(max_workers=10) as pool:
        pool.map(batch_event, cut_evts)

    ic()


if __name__ == "__main__":
    get_SAC("cut_event", "SAC", "event.lst", "station.lst")

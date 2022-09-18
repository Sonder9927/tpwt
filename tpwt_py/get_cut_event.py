from concurrent.futures import ThreadPoolExecutor
from icecream import ic
from pathlib import Path
import datetime as dt
import pandas as pd
import os, shutil
import subprocess

from pysrc.tpwt import get_binuse


"""
get event files and event dir
"""


def get_evt_drop(evt1, evt2):
    """
    get events between 30 and 120
    remove the same events in a period of 3 hours
    """
    evt_1 = pd.read_csv(evt1, usecols=["time", "latitude", "longitude"])
    evt_2 = pd.read_csv(evt2, usecols=["time", "latitude", "longitude"])
    evt = pd.concat([evt_1, evt_2]).drop_duplicates(keep=False)
    evt.index = pd.to_datetime(evt["time"])

    temp = sorted(evt.index)
    drop_lst = set()
    for i in range(len(temp)-1):
        du = (temp[i+1] - temp[i]).total_seconds()
        if du < 10800:
            drop_lst.update(temp[i: i+2])

    evt.drop(drop_lst, inplace=True)

    return evt


def time_convert(val: str, form: str) -> str:
    time = dt.datetime.strptime(val, "%Y-%m-%dT%H:%M:%S")
    return dt.datetime.strftime(time, form)


def get_evt_cat(evt, form):
    evt = evt.apply(lambda x: time_convert(str(x)[:19], form))
    evt.to_csv("event.cat", sep=" ", header=False, index=False)


def get_evt_lst(evt, form):
    evt["time"] = evt["time"].apply(lambda x: time_convert(str(x)[:19], form))
    evt[["longitude","latitude"]] = evt[["latitude","longitude"]]
    evt.to_csv("event.lst", sep=" ", header=False, index=False)


def get_event_file(event_1, event_2):
    """
    event.cat for cut event
    event.lst for tpwt
    """
    ic("getting event files for cut event and tpwt...")
    # Get evt which has no same events in a period of 3 hours.
    evt = get_evt_drop(event_1, event_2)

    cat_form = "%Y/%m/%d,%H:%M:%S"
    lst_form = "%Y%m%d%H%M"
    with ThreadPoolExecutor(max_workers=2) as pool:
        pool.submit(get_evt_cat, evt["time"], cat_form)
        pool.submit(get_evt_lst, evt, lst_form)


###############################################################################


def batch_1Hz(file_path):
    """
    batch function for get_Z_1Hz 
    to down sample every target file
    which will be putted into z_dir
    """
    file_1 = only_Z_1Hz / f"{file_path.name}_1"

    s = f"r {file_path} \n"
    s += "decimate 5 \n"
    s += f"w {file_1} \n"
    s += "q \n"
    os.putenv("SAC_DISPLAY_COPYRIGHT", "0")
    subprocess.Popen(['sac'], stdin=subprocess.PIPE).communicate(s.encode())


def get_Z_1Hz(data, patterns):
    """
    from data get only Z component sac file and downsample to 1 Hz 
    will put into only_Z_1Hz
    cut by event created by two csv files
    """
    ic("getting only_Z_1Hz...")
    # clear and re-create
    if only_Z_1Hz.exists():
        shutil.rmtree(only_Z_1Hz)
    only_Z_1Hz.mkdir(parents=True)

    files_lst = []
    for pattern in patterns:
        files_lst += list(Path(data).rglob(pattern))

    with ThreadPoolExecutor(max_workers=10) as pool:
        pool.map(batch_1Hz, files_lst)
    

###############################################################################


def batch_cut_event(sacs: list, id: int):
    """
    batch function for cut_event 
    """
    ic(id)
    lst = f"data_z.lst_{id}"
    db = f"data_z.db_{id}"
    done_lst = f"done_z.lst_{id}"
    # catalog (time reference to cut data)
    cat = "event.cat"

    with open(lst, "w+") as f:
        for sac in sacs:
            f.write(f"{sac}\n")

    mktraceiodb = get_binuse('mktraceiodb')
    cutevent = get_binuse('cutevent')

    cmd_string = 'echo shell start\n'
    cmd_string += f'{mktraceiodb} -L {done_lst} -O {db} -LIST {lst} -V\n'  # no space at end!
    cmd_string += f'{cutevent} '
    cmd_string += f'-V -ctlg {cat} -tbl {db} -b +0 -e +10800 -out {cut_dir}\n'
    cmd_string += 'echo shell end'
    subprocess.Popen(
        ['bash'],
        stdin = subprocess.PIPE
    ).communicate(cmd_string.encode())

    for file in [lst, db, done_lst]:
        os.remove(file)


def get_event_dir():
    """
    cut event from only_Z_1Hz using event.cat
    and result is in cut_dir
    """
    ic("getting cutted events...")
    if cut_dir.exists():
        shutil.rmtree(cut_dir)
    cut_dir.mkdir()

    # get list of mseed/SAC files (direcroty and file names)
    sacs = list(only_Z_1Hz.rglob("*_1"))
    # batch process
    batch = 1000
    sacs_batch_list = [sacs[i: i+batch] for i in range(0, len(sacs), batch)]
    with ThreadPoolExecutor(max_workers=10) as pool:
        pool.map(
            batch_cut_event,
            sacs_batch_list,
            [str(i) for i in range(len(sacs_batch_list))]
        )


###############################################################################


def get_cut_event(evt_30, evt_120, z_dir, evt_dir, data, patterns):
    """
    get event.cat and event.lst from two event catalog files of 30 and 120
    down sample sac files with only Z component from data to 1Hz
    cut event using event.cat
    """
    global only_Z_1Hz, cut_dir
    # direcroty for sac files with only Z component and 1Hz
    only_Z_1Hz = Path(z_dir)
    # output directory for cutted data
    cut_dir = Path(evt_dir)

    get_event_file(evt_30, evt_120)

    get_Z_1Hz(data, patterns)

    get_event_dir()

    ic()


if __name__ == "__main__":
    get_cut_event("event_30.csv", "event_120.csv", "only_Z_1Hz", "cut_event",
        "/path/to/data", ["*BD*Z.SAC", "*BD*Z.sac"])

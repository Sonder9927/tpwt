from icecream import ic
from threading import Thread, Lock
import pandas as pd
import os, pathlib

# My scripts
# functions
from pysrc.get_param import get_param_json

# classes
from pysrc.get_param import Param

"""
03
"""

def find_events(file_name: str, dir_name: str) -> list:
    """
    Return a list of events
    that are in both file_name and dir_name.
    """
    fd = pd.read_csv(
        file_name,
        sep='\s+',
        usecols=[0],
        names = ['evt'],
        engine='python'
    )
    file_events = [str(i) for i in fd['evt']]

    dir_events = os.listdir(dir_name)

    return [e for e in dir_events if e in file_events]


def find_stations(sta_file, area):
    """
    Return a list of stations in the sta_file
    that are in the area.
    """
    stas = pd.read_csv(
        sta_file,
        sep='\s+',
        names = ['sta_name', 'lo', 'la'],
        engine='python'
    )

    sta_in_area = stas[
        (stas['la'] >= area['sourth'])
        & (stas['la'] <= area['north'])
        & (stas['lo'] >= area['west'])
        & (stas['lo'] <= area['east'])
    ]

    return [i for i in sta_in_area['sta_name']]

    
##############################################################################


def get_temmper(p, evt: str, stas: list):
    """
    Tempper contains valid sac files in a event.
    """
    # get sac files list
    filelist = pathlib.Path(p.sac) / evt / 'filelist'
    if os.path.exists(filelist):
        with open(filelist, 'r') as f:
            sacs = f.read().splitlines()
    else:
        err_description = f'No filelist found in {evt}.'
        err_description += 'Please make sure you have finished tpwt step 1.'
        raise Exception(err_description)

    targets = [i for sta in stas if (i := f'{evt}.{sta}.LHZ.sac') in sacs]

    return targets


def process_event_tempper(p, evt: str, stas: list, lock):
    global temppers
    tempper = get_temmper(p, evt, stas)

    if len(tempper) <= p.nsta:
        ic(evt, "not enough stations")
    else:
        lock.acquire()
        temppers[evt] = tempper
        lock.release()

    ic(evt, "done")


def process_events_tempper(param, events, stations):
    global temppers
    temppers = {}
    # need a lock for the dict temppers
    lock = Lock()

    thread_list = []
    for event in events:
        t = Thread(
            target = process_event_tempper,
            args = [param, event, stations, lock]
        )
        thread_list.append(t)
        t.start()

    for t in thread_list:
        t.join()


##############################################################################


def write_event_eqlistper(sac_dir, evt_num, evt, lock):
    # get content for write into file eqlistper
    # the first line for every valid event is
    # total number of sac files exists, evt_num
    content = f'    {len(temppers[evt])} {evt_num + 1}\n'

    # sac files' position will follow it
    evt_dir = sac_dir / evt
    for sac in temppers[evt]:
        content += f'{evt_dir/sac}\n'

    # write content into file
    lock.acquire()
    with open(eqlistper, 'a') as f:
        f.write(content)
    lock.release()
    

def write_events_eqlistper(sac_dir):
    global eqlistper
    eqlistper = sac_dir / 'eqlistper'
    # need a lock for the file eqlistper
    lock = Lock()

    # first line
    with open(eqlistper, 'w') as f:
        f.write(f'{len(temppers)}\n')

    thread_list = []
    for evt_num, evt in enumerate(sorted([*temppers])):
        t = Thread(
            target = write_event_eqlistper,
            args = [sac_dir, evt_num, evt, lock]
        )
        thread_list.append(t)
        t.start()

    for t in thread_list:
        t.join()


def get_eqlistper(param, events, stations):
    # process every event
    # find valid events
    process_events_tempper(param, events, stations)
    
    # write eqlistper
    sac_dir = pathlib.Path.cwd() / param.sac
    write_events_eqlistper(sac_dir)

    # mark finish
    pathlib.Path('flag_eqlistper').touch()
    ic("Flag eqlistper done.")


def tpwt_03(param_json):
    # instancs a parameters class
    p3 = Param
    # get parameters
    param = get_param_json(param_json)
    # files
    p_f = param['files']
    p3.evt = p_f["evt"]
    p3.sta = p_f["sta"]
    p3.sac = p_f['sac']
    # immutables
    p_immu = param['immutables']
    p3.nsta = p_immu['nsta_cutoff']
    p3.region = p_immu['region']

    # flag_sta_dist
    if os.path.exists('flag_eqlistper'):
        ic('The flag_eqlistper existed, will skip running this part.')
    else:
        if (os.path.exists(p3.sta)
            and os.path.exists(p3.evt)):
            events = find_events(p3.evt, p3.sac)
            stations = find_stations(p3.sta, p3.region)
            get_eqlistper(p3, events, stations)
        else:
            raise Exception('No station.lst or event.lst found.')
    
    ic("TPWT step 3 done")


if __name__ == "__main__":
    tpwt_03("param.json")

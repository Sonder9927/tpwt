from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from icecream import ic
import pandas as pd

from tpwt_p.check import check_exists
from tpwt_p.rose import glob_patterns


def mk_eqlistper(sac_dir: Path, evts, stas, region, nsta) -> Path:
    # sourcery skip: inline-immediately-returned-variable
    events = find_events(evts, sac_dir)
    stations = find_stations(stas, region)

    # process every event
    # find valid events
    temppers = process_events_tempper(sac_dir, events, stations, nsta)

    # write eqlistper
    eqlistper = write_events_eqlistper(sac_dir, temppers)

    return eqlistper


###############################################################################


def process_events_tempper(sac_dir: Path, events, stas, nsta) -> dict:
    temppers = {}

    with ThreadPoolExecutor(max_workers=10) as executor:
        for e in events:
            future = executor.submit(process_event_tempper, sac_dir, e, stas, nsta)
            temppers |= future.result()
    return temppers


def write_events_eqlistper(sac_dir: Path, temppers: dict):
    eqlistper = Path("target/eqlistper")

    with open(eqlistper, "w+") as f:
        # first line
        f.write(f"{len(temppers)}\n")

        evt_list = sorted([*temppers])

        with ThreadPoolExecutor(max_workers=10) as executor:
            for i, e in enumerate(evt_list):
                future = executor.submit(write_event_eqlistper, temppers, sac_dir, e, i + 1)
                f.write(future.result())

    return eqlistper


##############################################################################
"""
batch function
"""


def process_event_tempper(data: Path, evt, stas, nsta) -> dict:
    """
    batch function
    """
    filelist = check_exists(data / evt / "filelist")

    with open(filelist, "r") as f:
        sacs = f.read().splitlines()

    tempper = [sac for sta in stas if (sac := f"{evt}.{sta}.LHZ.sac") in sacs]

    if len(tempper) > nsta:
        # ic(evt, "done")
        return {evt: tempper}
    ic(evt, "not enough stations")
    return {}


def write_event_eqlistper(temppers: dict, sac_dir: Path, evt, evt_id: int):
    """
    batch function
    get content for write into file eqlistper
    the first line for every valid event is
    total number of sac files exists, evt_num
    """
    tems_evt = temppers[evt]
    content = f"    {len(tems_evt)} {evt_id}\n"

    # sac files' position will follow it
    evt_dir = sac_dir / evt
    for sac in tems_evt:
        content += f"{evt_dir/sac}\n"

    return content


##############################################################################


def find_events(evts: pd.DataFrame, sac_dir: Path) -> list:
    """
    Return a list of events
    that are in both file_name and dir_name.
    """
    evts_dir = pd.DataFrame(
        data=[e.name for e in glob_patterns("glob", sac_dir, ["20*/"])], columns=["sta"]
    )

    events_df = pd.concat([evts, evts_dir]).drop_duplicates(keep=False)
    return events_df.sta.dropna().unique()


def find_stations(stas, area):
    """
    Return a list of stations in the sta_file
    that are in the area.
    """
    sta_in_area = stas[
        (stas.la >= area.south)
        & (stas.la <= area.north)
        & (stas.lo >= area.west)
        & (stas.lo <= area.east)
    ]

    return list(sta_in_area["sta"])

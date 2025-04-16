from pathlib import Path

import pandas as pd


def make_eqlist(sac_dir: Path, evt_df, sta_df, region, nsta, eqlist):
    events = _find_events(evt_df, sac_dir)
    stations = _find_stations(sta_df, region)
    # process every event
    # find valid events
    temppers = make_event_temppers(sac_dir, events, stations, nsta)

    # write eqlistper
    make_event_eqlists(sac_dir, temppers, eqlist)

    return eqlist


###############################################################################


def make_event_temppers(
    sac_dir: Path, events: list[str], stas: list[str], nsta: int
) -> dict[str, list[str]]:
    temppers = {}
    for evt in events:
        filelist = sac_dir / evt / "filelist"

        with filelist.open() as f:
            sacs = f.read().splitlines()

        tempper = [sac for sta in stas if (sac := f"{evt}.{sta}.LHZ.sac") in sacs]

        if len(tempper) < nsta:
            continue
        temppers[evt] = tempper
    return temppers


def make_event_eqlists(sac_dir: Path, temppers: dict, eqlist: Path):
    contents = []
    evt_list = sorted([*temppers])
    for i, evt in enumerate(evt_list):
        tems_evt = temppers[evt]
        contents.append(f"    {len(tems_evt)} {i + 1}\n")
        # sac files' position will follow it
        evt_dir = sac_dir / evt
        contents += [f"{evt_dir / sac}\n" for sac in tems_evt]

    with eqlist.open("w+") as f:
        # first line
        f.write(f"{len(temppers)}\n")
        # contents
        f.writelines(contents)


##############################################################################


def _find_events(evts: pd.DataFrame, sac_dir: Path) -> list:
    """
    Return a list of events
    that are in both file_name and dir_name.
    """
    evts_in_dir = pd.DataFrame(
        data=[dd.name for dd in sac_dir.iterdir() if dd.is_dir()], columns=["time"]
    )

    events_df = pd.concat([evts, evts_in_dir]).drop_duplicates(keep=False)
    return events_df.time.dropna().unique()


def _find_stations(sta_df: pd.DataFrame, region):
    """
    Return a list of stations in the sta_file
    that are in the area.
    """
    sta_in_area = sta_df[
        (sta_df.latitude >= region.south)
        & (sta_df.latitude <= region.north)
        & (sta_df.longitude >= region.west)
        & (sta_df.longitude <= region.east)
    ]

    return sta_in_area["sta"].to_list()

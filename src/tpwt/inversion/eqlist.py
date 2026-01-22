from pathlib import Path
from typing import List, Dict, Set

import pandas as pd


def make_eqlist(sac_dir: Path, evt_df, sta_df, region, nsta, eqlist):
    events = _find_events(evt_df, sac_dir)
    stations = _find_stations(sta_df, region)
    # process every event
    # find valid events
    temppers = _process_events(sac_dir, events, set(stations), nsta)

    # write eqlistper
    _write_eqlists(sac_dir, temppers, eqlist)

    return eqlist


###############################################################################


def _process_events(
    sac_dir: Path, events: List[str], stas: Set[str], nsta: int
) -> Dict[str, List[str]]:
    return {
        evt: valid_sacs
        for evt in events
        if len(valid_sacs := _get_valid_sacs(sac_dir, evt, stas)) >= nsta
    }


def _get_valid_sacs(sac_dir: Path, evt: str, stas: Set[str]) -> List[str]:
    file_path = sac_dir / evt / "filelist"
    try:
        with file_path.open() as f:
            return [
                f"{evt}.{sta}.LHZ.sac"
                for sac in f.read().splitlines()
                if (sta := sac.split(".")[1]) in stas
            ]
    except FileNotFoundError:
        return []


def _write_eqlists(sac_dir: Path, temppers: Dict[str, List[str]], eqlist: Path):
    with eqlist.open("w") as f:
        # first line
        f.write(f"{len(temppers)}\n")
        contents = (
            f"    {len(files)} {i}\n" + "\n".join(f"{sac_dir / evt / f}" for f in files)
            for i, (evt, files) in enumerate(sorted(temppers.items()), 1)
        )
        # contents
        f.write("\n".join("\n".join([header] + paths) for header, *paths in contents))


def _find_events(evt_df: pd.DataFrame, sac_dir: Path) -> list:
    """
    Return a list of events
    that are in both file_name and dir_name.
    """
    sac_events = {d.name for d in sac_dir.iterdir() if d.is_dir()}
    return evt_df[evt_df["time"]].is_in(sac_events)["time"].to_list()


def _find_stations(sta_df: pd.DataFrame, region):
    """
    Return a list of stations in the sta_file
    that are in the area.
    """
    return sta_df[
        sta_df.longitude.between(region.west, region.east)
        & sta_df.latitude.between(region.south, region.north)
    ]["station"].to_list()

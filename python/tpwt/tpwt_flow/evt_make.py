import datetime as dt
import random
from pathlib import Path

import obspy
import pandas as pd
from icecream import ic


class EvtMaker:
    pattern = "%Y-%m-%dT%H:%M:%S"
    header = ("time", "longitude", "latitude", "depth", "mag")

    def __init__(self, evt1, evt2, time_delta):
        ic("Hello, this is EVT maker.")
        self.evt = self.evt_out_time(evt1, evt2, time_delta)

    @classmethod
    def evt_out_time(cls, evt1, evt2, time_delta):
        evt1 = pd.read_csv(evt1, usecols=cls.header)
        evt2 = pd.read_csv(evt2, usecols=cls.header)
        evt = pd.concat([evt1, evt2]).drop_duplicates(keep=False)
        if evt is None:
            raise ValueError(f"no data found between {evt1} and {evt2}!")
        evt.index = pd.to_datetime(evt["time"])
        temp = sorted(evt.index)

        drop_lst = set()
        for i in range(len(temp) - 1):
            du = (temp[i + 1] - temp[i]).total_seconds()
            if du < time_delta:
                drop_lst.update(temp[i : i + 2])

        return evt.drop(drop_lst)  # pyright: ignore  # noqa: PGH003

    @classmethod
    def time_convert(cls, val: str, form: str) -> str:
        time = dt.datetime.strptime(val, cls.pattern)
        return dt.datetime.strftime(time, form)

    def extract(self, form, cols: list[str] | None = None) -> pd.DataFrame:
        if cols is None:
            cols = list(self.header)
        evt = self.evt[cols].copy()
        evt["time"] = evt["time"].apply(
            lambda x: self.time_convert(str(x)[:19], form)
        )
        return evt


def head_from_sac(sac_dir: str | Path) -> None:
    all_names = set()
    find_names = set()
    evt_data = []
    sta_data = []
    for sac_file in Path(sac_dir).rglob("*.sac"):
        [evt_name, sta_name, _] = sac_file.stem.split(".")
        all_names |= {evt_name, sta_name}
        if evt_name not in find_names:
            stream = obspy.read(sac_file)
            trace = stream[0]
            head = trace.stats.sac
            try:
                evlo = head["evlo"]
                evla = head["evla"]
            except KeyError:
                continue
            evmag = head.get("mag") or round(random.uniform(5.5, 9.0), 1)
            evt_data.append([evt_name, evlo, evla, evmag])
            find_names.add(evt_name)
        if sta_name not in find_names:
            stream = obspy.read(sac_file)
            trace = stream[0]
            head = trace.stats.sac
            try:
                stlo = head["stlo"]
                stla = head["stla"]
            except KeyError:
                continue
            sta_data.append([sta_name, stlo, stla])
            find_names.add(sta_name)

    evdf = pd.DataFrame(evt_data, columns=["name", "lo", "la", "mag"])
    evdf.to_csv("event.csv", index=False)
    stdf = pd.DataFrame(sta_data, columns=["name", "lo", "la"])
    stdf.to_csv("station.csv", index=False)
    err_names = all_names - find_names
    ic(err_names)

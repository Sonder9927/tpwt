import datetime as dt

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
        evt["time"] = evt["time"].apply(lambda x: self.time_convert(str(x)[:19], form))
        return evt

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd

import obspy
from icecream import ic


class Checker:
    channel = "LHZ"
    evtn = 12
    d30 = 111 * 30
    d120 = 111 * 120
    check_targets = ("channel", "evtn", "sta", "dist")

    def __init__(self) -> None:
        ic("Checker!")

    @classmethod
    def _bcheck_head(cls, sacs: list[Path]):
        err = dict(zip(cls.check_targets, [[]] * len(cls.check_targets)))
        for sac in sacs:
            [evt, sta, cfn] = sac.stem.split(".")
            st = obspy.read(sac)
            tr = st[0]
            head = tr.stats.sac
            # check channel
            if cfn != head["KCMPNM"]:
                err["channel"].append(sac)
            # check evtn
            if len(evt) != cls.evtn:
                err["evtn"].append(sac)
            # check sta
            if sta != head["KSTNM"]:
                err["sta"].append(sac)
            # check dist
            dist = head.get("dist")
            if any([dist is None, dist < cls.d30, dist > cls.d120]):
                err["dist"].append(sac)
        return err

    def check_heads(self, sac_dir):
        err = dict(zip(self.check_targets, [[]] * len(self.check_targets)))

        sacs = list(Path(sac_dir).rglob("*.sac"))
        bsacs = [sacs[i : i + 1000] for i in range(0, len(sacs), 1000)]
        with ThreadPoolExecutor(max_workers=20) as pl:
            futures = [pl.submit(self._bcheck_head, bs) for bs in bsacs]
            for future in as_completed(futures):
                res = future.result()
                for k, v in res.items():
                    err[k] += v
        ic(err)

    def check_lst(self, sac_dir, *, evt_lst, sta_lst):
        lst_err = []
        sacs = list(Path(sac_dir).rglob("*.sac"))
        bsacs = [sacs[i : i + 1000] for i in range(0, len(sacs), 1000)]
        evts = pd.read_csv(
            evt_lst,
            header=None,
            delim_whitespace=True,
            usecols=[0, 3],
            names=["name", "mag"],
        )
        stas = pd.read_csv(
            sta_lst, header=None, delim_whitespace=True, usecols=[0], names=["name"]
        )
        all_lst = evts["name"].tolist() + stas["names"].tolist()
        with ThreadPoolExecutor(max_workers=20) as pl:
            futures = [pl.submit(_bcheck_lst, bs, all_lst) for bs in bsacs]
            for future in as_completed(futures):
                res = future.result()
                lst_err += res
        ic(lst_err)
        df = evts[evts["mag"] < 5 or evts["mag"] > 9]
        mag_err = df["name"].tolist()
        ic(mag_err)


def _bcheck_lst(sacs, lst) -> list[str]:
    err_lst = []
    for sac in sacs:
        [evt, sta, _] = sac.stem.split(".")
        if evt not in lst:
            err_lst.append(evt)
        if sta not in lst:
            err_lst.append(sta)

    return err_lst

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import pandas as pd

import obspy
from icecream import ic
import json


class Checker:
    channel = "LHZ"
    evtn = 12
    d30 = 111 * 30
    d120 = 111 * 120
    check_targets = ("channel", "evtn", "sta", "dist")
    check_log = Path("log/check_log.json")

    def __init__(self) -> None:
        self.info: list[dict[str, list[str]]] = []
        ic("Checker!")

    @classmethod
    def _err_dict(cls) -> dict[str, list[str]]:
        return {tt: [] for tt in cls.check_targets}

    @classmethod
    def _bcheck_head(cls, sacs: list[Path]) -> dict[str, list[str]]:
        err = cls._err_dict()
        for sac in sacs:
            [evt, sta, clf] = sac.stem.split(".")
            st = obspy.read(sac)
            tr = st[0]
            head = tr.stats.sac
            # check channel
            cl = head.get("kcmpnm")
            if any([clf != cls.channel, cl is None, cl != clf]):
                err["channel"].append(str(sac))
            # check evt
            if len(evt) != cls.evtn or evt != sac.parent.name:
                ic(evt, sac.parent.name)
                err["evtn"].append(str(sac))
            # check sta
            hsta = head.get("kstnm")
            if hsta is None or sta != hsta:
                err["sta"].append(str(sac))
            # check dist
            dist = head.get("dist")
            if any([dist is None, dist < cls.d30, dist > cls.d120]):
                err["dist"].append(str(sac))
        return err

    @staticmethod
    def _bcheck_lst(sacs, lst_names) -> set[str]:
        names = set()
        for sac in sacs:
            [evt, sta, _] = sac.stem.split(".")
            names |= {evt, sta}
        return {name for name in names if name not in lst_names}

    def log_info(self, outfile=None) -> None:
        ff = outfile or self.check_log
        with open(ff, "w") as f:
            json.dump(self.info, f, indent=2)
        ic(f"see log file: {ff}")

    def check_heads(self, sac_dir):
        head_err = self._err_dict()
        sacs = list(Path(sac_dir).rglob("*.sac"))
        bsacs = [sacs[i : i + 10000] for i in range(0, len(sacs), 10000)]
        with ThreadPoolExecutor(max_workers=20) as pl:
            futures = [pl.submit(self._bcheck_head, bs) for bs in bsacs]
            for future in as_completed(futures):
                res = future.result()
                for k, v in res.items():
                    head_err[k] += v
        self.info.append(head_err)

    def check_lst(self, sac_dir, *, evf: str, stf: str):
        lst_err = set()
        sacs = list(Path(sac_dir).rglob("*.sac"))
        bsacs = [sacs[i : i + 10000] for i in range(0, len(sacs), 10000)]
        evts = pd.read_csv(evf, dtype={"name": str})
        stas = pd.read_csv(stf, dtype={"name": str})
        lst_names = evts["name"].tolist() + stas["name"].tolist()
        with ThreadPoolExecutor(max_workers=20) as pl:
            futures = [pl.submit(self._bcheck_lst, bs, lst_names) for bs in bsacs]
            for future in as_completed(futures):
                res = future.result()
                lst_err |= res
        df = evts[(evts["mag"] < 5) | (evts["mag"] > 9)]
        mag_err = df["name"].tolist()
        self.info.append({"lst_err": list(lst_err), "mag_err": mag_err})

"""sac formatter
This script will move events directories having 14 numbers in cut_dir to sac_dir
and batch rename a group of sac files in given directory renamed with 12 numbers.

From 
TE.BD917.00.HHZ.D.2022001105112.sac
To
event.station.LHZ.sac

Then add information of both event and station to head of sac files in SAC directory
"""

# author : Sonder Merak
# created: 6th April 2022
# version: 2.0

import os
import shutil
import subprocess
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from pathlib import Path

import pandas as pd
from icecream import ic
from tqdm import tqdm

from tpwt.rose import glob_patterns, path, re_create_dir

from .obs_mod import Obs


class Pos:
    def __init__(self, x, y, z=None) -> None:
        self.x = x
        self.y = y
        self.z = z


class SacHead:
    channel = "LHZ"

    def __init__(self, evf, stf) -> None:
        evt = pd.read_csv(evf, dtype={"name": str}, index_col="name")
        sta = pd.read_csv(stf, dtype={"name": str}, index_col="name")
        self.sites = pd.concat([sta, evt])

    def site(self, evt, sta):
        stpos = self.sites.loc[sta]
        evpos = self.sites.loc[evt]
        return evpos, stpos

    def ch_cmd(self, sac, evt, sta) -> str:
        evpos, stpos = self.site(evt, sta)
        # ch evla, evlo, evdp(optional) and stla, stlo, stel(optional)
        s = "wild echo off \n"
        s += f"r {sac} \n"
        s += f"ch evlo {evpos['lo']}\n"
        s += f"ch evla {evpos['la']}\n"
        s += f"ch mag {evpos['mag']}\n"
        if evpos.get("dp") is not None:
            s += f"ch evdp {evpos['dp']}\n"
        s += f"ch stlo {stpos['lo']}\n"
        s += f"ch stla {stpos['la']}\n"
        if stpos.get("el") is not None:
            s += f"ch stel {stpos['el']}\n"
        s += f"ch kcmpnm {self.channel}\n"
        s += f"ch kstnm {sta}\n"
        s += "wh \n"
        s += "q \n"
        return s

    def re_ch_sacs(self, sacs: list[Path]) -> list[str]:
        """
        change head of sac file to generate dist information
        """
        err_sacs = []
        for sac in tqdm(sacs):
            [evt, sta, channel] = sac.stem.split(".")
            if channel != self.channel:
                sac = sac.rename(sac.parent / f"{evt}.{sta}.{self.channel}.sac")
            cmds = self.ch_cmd(sac, evt, sta)
            try:
                os.putenv("SAC_DISPLAY_COPYRIGHT", "0")
                subprocess.Popen(["sac"], stdin=subprocess.PIPE).communicate(
                    cmds.encode()
                )
            except Exception:
                err_sacs.append(str(sac))
                ic("err:", str(sac))
        return err_sacs


class SacFormatter:
    def __init__(self) -> None:
        ic("Hello, this is SAC formatter")

    def make_sac(self, data: str | Path, dir: str):
        data = Path(data)
        # clear and re-create
        target = path.remake(dir)
        ic(target)

    def format(self, dir: str, *, evf, stf):
        sacs = list(Path(dir).rglob("*.sac"))
        head = SacHead(evf, stf)
        size = 10_000
        bsacs = [sacs[i : i + size] for i in range(0, len(sacs), size)]
        err_sacs = []
        with ProcessPoolExecutor(max_workers=10) as pool:
            futures = [pool.submit(head.re_ch_sacs, bs) for bs in bsacs]
            for future in as_completed(futures):
                res = future.result()
                err_sacs += res

            pool.map(head.re_ch_sacs, bsacs)
        return err_sacs


class oldSacFormatter:
    def __init__(self, data, *, evt, sta) -> None:
        self.channel = "LHZ"
        self.data = Path(data)
        self.evt = pd.read_csv(
            evt,
            delim_whitespace=True,
            names=["evt", "lo", "la", "dp"],
            dtype={"evt": str},
            header=None,
            index_col="evt",
        )
        self.sta = pd.read_csv(
            sta,
            delim_whitespace=True,
            names=["sta", "lo", "la"],
            header=None,
            index_col="sta",
        )
        ic("Hello, this is SAC formatter")

    def make_sac(self, dir: str):
        # clear and re-create
        target = re_create_dir(dir)
        self.format_to_dir(target)
        self.dist_km_filter(target)

    def filter_event_lst(self, dir: str, el: str):
        tp = Path(dir)
        if not tp.exists():
            raise FileNotFoundError(f"Not found {tp}!")

        evt_use = [d.name for d in tp.glob("*/**")]
        evt_all = self.evt.index.to_list()

        drop_lst = [e for e in evt_all if e not in evt_use]
        evt = self.evt.drop(drop_lst)
        evt.to_csv(el, header=False, sep=" ")

    def format_to_dir(self, target: Path):
        # get list of events directories
        cut_evts = glob_patterns("glob", self.data, ["*/**"])
        stas = self.sta_to_points()
        err_sta = set()

        with ProcessPoolExecutor(max_workers=10) as executor:
            for e in cut_evts:
                ep = self.evt_to_point(e.name[:12])
                future = executor.submit(batch_event, target, e, ep, stas, self.channel)
                err_sta.update(future.result())
        ic(err_sta)

    def dist_km_filter(self, dp: Path):
        sacs = list(dp.rglob("*.sac"))
        sacss = [sacs[i:200] for i in range(0, len(sacs), 200)]
        with ThreadPoolExecutor(max_workers=10) as executor:
            executor.map(batch_dist, sacss)

    def evt_to_point(self, evt: str) -> Pos:
        return Pos(x=self.evt.lo[evt], y=self.evt.la[evt], z=self.evt.dp[evt])

    def sta_to_points(self) -> dict[str, Pos]:
        dk = self.sta.index
        dv = [Pos(x=self.sta.lo[i], y=self.sta.la[i]) for i in dk]
        return dict(zip(dk, dv))


def batch_event(out_dir, cut_evt, ep, stas, channel):
    """
    batch function to process every event
    move events directories
    format sac files
    """
    # move
    sac_evt = out_dir / cut_evt.name[:12]
    shutil.copytree(cut_evt, sac_evt)

    # process every sac file
    sacs = glob_patterns("glob", sac_evt, ["*"])
    err_sta = set()

    with ThreadPoolExecutor(max_workers=10) as pool:
        for sac in sacs:
            future = pool.submit(rename_ch, sac, ep, stas, channel)
            res = future.result()
            if res:
                err_sta.update([res])

    return err_sta


# !This step can be putted into batch_event later.
def batch_dist(sacs: list[Path]):
    # rad = 111
    # rad30 = rad * 30
    # rad120 = rad * 120
    # for sp in sacs:
    #     sac = Ses(str(sp))
    #     dist = sac.dist_km
    #     if dist < rad30 or dist > rad120:
    #         sp.unlink()
    pass


###############################################################################


def rename_ch(sac, ep, stas, channel):
    # rename
    sta_name, sac_new = format_sac_name(sac, channel)

    # change head
    sp = stas.get(sta_name)
    if sp == None:
        sac.unlink()
        return sta_name
    else:
        shutil.move(sac, sac_new)
        ch_sac(sac_new, ep, sp, sta_name, channel)
        # ch_obspy(res.sac, p.evt, p.stas[res.sta], p.channel)
        return None


def format_sac_name(target: Path, channel):
    """
    rename and ch sac files
    """
    evt_name = target.parent.name
    sta_name = target.name.split(".")[1].upper()
    new_name = f"{evt_name}.{sta_name}.{channel}.sac"

    target_new = target.parent / new_name

    return sta_name, target_new


def ch_sac(target: Path, evt: Pos, sta: Pos, sta_name, channel):
    """
    change head of sac file to generate dist information
    """
    # ch evla, evlo, evdp(optional) and stla, stlo, stel(optional)

    s = "wild echo off \n"
    s += "r {} \n".format(target)
    s += f"ch evlo {evt.x}\n"
    s += f"ch evla {evt.y}\n"
    if evt.z is not None:
        s += f"ch evdp {evt.z}\n"
    s += f"ch stlo {sta.x}\n"
    s += f"ch stla {sta.y}\n"
    # s += f"ch stel {sta.z}\n"
    s += f"ch kcmpnm {channel}\n"
    s += f"ch kstnm {sta_name}\n"
    s += "wh \n"
    s += "q \n"

    os.putenv("SAC_DISPLAY_COPYRIGHT", "0")
    subprocess.Popen(["sac"], stdin=subprocess.PIPE).communicate(s.encode())


def ch_obspy(target: Path, evt: Pos, sta: Pos, channel):
    """
    change head of sac file to generate dist information
    """
    # ch evla, evlo, evdp(optional) and stla, stlo, stel(optional)
    obs = Obs(target, evt, sta, channel)
    obs.ch_obs()

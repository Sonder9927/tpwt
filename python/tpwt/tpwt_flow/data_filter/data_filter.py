from pathlib import Path

from tpwt_p.rose import read_xyz

from .calculate import calculate_dispersion
from .aftan_snr import process_events_aftan_snr
from .sta_dist import process_periods_sta_dist
from .mk_eq_list import mk_eqlistper


class Data_Filter:
    def __init__(self, param) -> None:
        self.param = param
        ef = self.param.target("evt_lst")
        sf = self.param.target("sta_lst")
        self.evts = read_xyz(ef, ["sta", "lo", "la"])
        self.stas = read_xyz(sf, ["sta", "lo", "la"])

    def filter(self):
        self.calculate_dispersion()
        self.aftan_snr()
        self.sta_dist()
        self.mk_eqlistper()

    def calculate_dispersion(self, disp_list=[]):
        """
        genetate inter-station dispersion curves using the GDM model.
        """
        path = self.param.target("path")
        calculate_dispersion(sta_v2(self.evts), sta_v2(self.stas), path, disp_list)
        return "Flag GDM52 done."

    def aftan_snr(self):
        """
        aftan_snr
        """
        path = self.param.target("path")
        sac_dir = self.param.target("sac")
        process_events_aftan_snr(sac_dir, path)

        return "Flag aftan_snr done."

    def sta_dist(self):
        # set snr and tcut
        process_periods_sta_dist(self.param)

    def mk_eqlistper(self):
        self.eq_list = mk_eqlistper(
            sac_dir=self.param.parameter("sac"),
            evts=self.evts["sta"],
            stas=self.stas,
            region=self.param.region(),
            nsta=self.param.parameter("nsta"),
        )
        return self.eq_list


def sta_v2(sta):
    sta[["lo", "la"]] = sta[["la", "lo"]]
    return sta

from collections import namedtuple

import pandas as pd
from icecream import ic
from rose import pather, logger

from .grid_nodes import inversion_nodes_TPWT
from .inverse import inverse_pre, inverse_run

Param_tpwt = namedtuple(
    "Param_twpt",
    "per vel snr tcut dist nsta smooth damping region "
    "eqlistper nodes staid all_events sens_dir tpwt_dir",
)


class TpwtInver:
    def __init__(self, param) -> None:
        """init

        Parameters:
            param (Param): Param class for TPWT program

        Note:
            param is made by `tpwt.lib.load_param` function
        """
        self.param = param
        self.log = logger("tpwt_inverse", "target/logs/tpwt_inverse.log")
        self.region = None

    def grid_nodes(self):
        """inversion nodes"""
        # create inversion grid nodes
        self.node_file = "target/inversion_nodes"
        region = self.param.region()

        # notice: `expanded` will return a list `[w,e,s,n]` but not change `Region`
        self.region = region.expanded(area_expand)
        region.expand(area_expand)
        inversion_nodes_TPWT(self.node_file, region)

    def senstivity_kernels(self, kernel: str = "gaussian"):
        """senstivity kernels

        Parameters:
            kernel: `["gaussian", "born"]`
        """

    def inverse(self):
        """inverse

        steps:
            1. initialize
            2. inverse
        """
        self.initialize()
        self.iter()

    def initialize(self, periods: list[int] = [], area_expand: float = 0.5):
        """pre inverse

        Preparation for inverse contains
        grid nodes, stationid, eqlistper, senstivity kernels.

        Args:
            periods: list of periods to be inverted (optional)
            area_expand: expand inverion region
        """
        # eqlistper file
        self.eqlistper = "target/eqlistper"

        # wave type: rayleigh or love
        # (this version only support rayleigh)
        self.wave_type = ["rayleigh", "love"][0]

        # stationid
        self.staid = "target/stationid.dat"
        staid = pd.read_csv(
            self.param.targets["sta_lst"],
            delim_whitespace=True,
            usecols=[0],
            header=None,
            engine="python",
        )
        staid.insert(loc=1, column="NR1", value=[i for i in range(1, len(staid) + 1)])
        staid.insert(loc=2, column="NR2", value=[i for i in range(1, len(staid) + 1)])
        staid.to_csv(self.staid, sep=" ", header=False, index=False)

        # some dirs
        # self.all_events = check_exists(self.param.target("all_events"))
        # ## these need to re-create to generate new results
        self.tpwt_dir = pather.redir(
            pather.twpt_dir(
                "TPWT",
                snr=self.snr,
                tcut=self.tcut,
                smooth=self.smooth,
                damping=self.damping,
            )
        )
        self.sens_dir = pather.redir("target/sens_dir")

        # preparation for inversion with periods
        # self.pers = self.param.model["periods"]
        # self.vels = self.param.model["vels"]
        # self.ds = dicts_of_per_vel(pers=self.pers, vels=self.vels)
        ## special cases
        # if periods:
        #     self.pers = periods
        #     ds = [d for d in self.ds if d['per'] in self.pers]
        # else:
        #     ds = self.ds

        # bind parameters
        # self.ps = [Param_tpwt(
        #     d["per"], d["vel"], self.snr, self.tcut, self.param.filter["dist"],
        #     self.param.filter["nsta"], self.smooth, self.damping, self.region,
        #     self.eqlistper, self.node_file, self.staid, self.all_events, self.tpwt_dir,
        #     self.sens_dir) for d in ds]

        # inverse_pre(self.ps)
        inverse_pre(
            self.param, self.eqlistper, self.node_file, self.staid, self.tpwt_dir
        )

    def iter(self, periods: list[int] | None = None, method: str = "rswt"):
        """TPWT inverse

        Args:
            periods: list of periods to be inverted (optional)
            method: inverse method (select in ["tpwt", "opwt", "rswt"])
        """
        # run tpwt with special periods or periods initialized(default)
        if periods:
            p_valid = set(periods) & set(self.pers)
            if p_valid:
                ps = [p for p in self.ps if p.per in p_valid]
            else:
                ic("No valid period found. Please check the periods when initializing.")
                return
            p_unvalid = set(periods) - p_valid
            ic(periods, p_valid, p_unvalid)
        else:
            ps = self.ps

        inverse_run(ps, method)

    def collect(self) -> pd.DataFrame:
        """collect grids

        Returns:
            dataframe of results of all periods TPWT inversion.
        """
        tpwt_dir = self.param.target("tpwt_dir")
        gridf = self.param.target("tpwt_file")

from collections import namedtuple
from icecream import ic
import pandas as pd

from tpwt_p.rose import get_dirname

from tpwt_p.rose import dicts_of_per_vel, re_create_dir
from tpwt_p.check import check_exists
from tpwt_r import Region

from .grid_nodes import inversion_nodes_TPWT
from .inverse import inverse_pre, inverse_run

Param_tpwt = namedtuple(
    "Param_twpt",
    "per vel snr tcut dist nsta smooth damping region "
    "eqlistper nodes staid all_events sens_dir tpwt_dir",
)


class TPWT_Iter:
    def __init__(self, param) -> None:
        self.param = param
        self.region = None

    def iter(self):
        self.initialize()
        self.inverse()

    def initialize(self, periods=[], area_expand=0.5):
        # create inversion grid nodes
        self.node_file = "target/inversion_nodes"
        region = self.param.region()

        # notice: `expanded` will return a list `[w,e,s,n]` but not change `Region`
        self.region = region.expanded(area_expand)
        region.expand(area_expand)
        inversion_nodes_TPWT(self.node_file, region)

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
        self.tpwt_dir = re_create_dir(
            get_dirname(
                "TPWT",
                snr=self.snr,
                tcut=self.tcut,
                smooth=self.smooth,
                damping=self.damping,
            )
        )
        self.sens_dir = re_create_dir("target/sens_dir")

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

    def inverse(self, periods=[], method="rswt"):
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

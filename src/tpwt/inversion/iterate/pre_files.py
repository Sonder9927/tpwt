from pathlib import Path
from typing import Tuple

import pandas as pd

from tpwt import TPWTConfig

from .eqlist import make_eqlist
from .grid_nodes import make_gridnode


def make_pre_files(cfg: TPWTConfig) -> Tuple[Path, Path, Path]:
    # make inversion grid nodes file
    gridnode = cfg.outpath / "inverse_node"
    dgrids = cfg.region.dgrids()
    make_gridnode(
        region=cfg.region.to_list(expand=0.5), dgrids=dgrids, outfile=gridnode
    )

    # read station df
    sta_df = pd.read_csv(cfg.paths["sta_csv"])
    # make stationid
    stationid = cfg.outpath / "stationid.dat"
    staid_df = sta_df[["station"]]
    staid_df.insert(loc=1, column="NR1", value=[i for i in range(1, len(staid_df) + 1)])
    staid_df.insert(loc=2, column="NR2", value=[i for i in range(1, len(staid_df) + 1)])
    staid_df.to_csv(stationid, sep=" ", header=False, index=False)

    # read event df
    evt_df = pd.read_csv(cfg.paths["evt_csv"])
    # make eqlist
    eqlist = cfg.outpath / "eqlist"
    make_eqlist(
        cfg.paths["sac_dir"],
        evt_df,
        sta_df,
        cfg.region.to_list(),
        cfg.params["nsta"],
        eqlist,
    )
    return eqlist, gridnode, stationid

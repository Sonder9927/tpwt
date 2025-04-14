from pathlib import Path
from typing import Optional

import pandas as pd

from tpwt import TPWTConfig

from .control import aftan_snr, calculate_dispersion, phase_amplitude
from .iterate import inverse_iter, make_eqlist, make_gridnode


def tpwt_iter(config: TPWTConfig):
    method = _valid_method(config.params.get("method"))
    eqlist, gridnode, stationid = _make_iter_files(config)
    binpath = config.paths.get("binpath", Path("TPWT/bin"))
    inverse_iter()


def inverse(config_toml: str):
    cfg = TPWTConfig(config_toml)
    quanlity_control(cfg)
    tpwt_iter(cfg)


def quanlity_control(config: TPWTConfig):
    binpath = config.paths.get("binpath", Path("TPWT/bin"))
    evt_df = pd.read_csv(config.paths["evt_csv"])
    sta_df = pd.read_csv(config.paths["sta_csv"])
    path_dir = Path("outputs/path")

    calculate_dispersion(
        evt_df=evt_df, sta_df=sta_df, path_dir=path_dir, binpath=binpath
    )
    aftan_snr(sac_dir=config.paths["sac_dir"], path_dir=path_dir, binpath=binpath)

    ph_amp_dir = Path("outputs/ph_amp_dir")
    phase_amplitude(
        config.periods(),
        config.paths["sac_dir"],
        evt_df,
        sta_df,
        ph_amp_dir,
        **config.get_params("snr", "tcut", "nsta", "cut_per", "dist"),
        region=config.region_list(),
        ref_sta=config.model["ref_sta"],
        binpath=binpath,
    )


def _make_iter_files(config: TPWTConfig) -> tuple[Path, Path, Path]:
    # make inversion grid nodes file
    gridnode = Path("outputs/inverse_node")
    dgrid = config.params.get("dgrid", [0.5, 0.5])
    make_gridnode(region=config.region_list(expand=0.5), dgrid=dgrid, outfile=gridnode)

    # read station df
    sta_df = pd.read_csv(config.paths["sta_csv"])
    # make stationid
    stationid = Path("outputs/stationid.dat")
    staid_df = sta_df[["station"]]
    staid_df.insert(loc=1, column="NR1", value=[i for i in range(1, len(staid_df) + 1)])
    staid_df.insert(loc=2, column="NR2", value=[i for i in range(1, len(staid_df) + 1)])
    staid_df.to_csv(stationid, sep=" ", header=False, index=False)

    # read event df
    evt_df = pd.read_csv(config.paths["evt_csv"])
    # make eqlist
    eqlist = Path("outputs/eqlist")
    make_eqlist(
        config.paths["sac_dir"],
        evt_df,
        sta_df,
        region=config.region_list(),
        nsta=config.params["nsta"],
        eqlist=eqlist,
    )
    return eqlist, gridnode, stationid


def _valid_method(method: Optional[str]) -> str:
    methods = ["TPWT", "OPWT"]
    # check method
    if method is None:
        method = methods[1]
        print(f"Use default method `{method}`")
    method = method.upper()
    if method not in methods:
        raise ValueError(f"Unvalid method: {method}, pick one in ")
    return method

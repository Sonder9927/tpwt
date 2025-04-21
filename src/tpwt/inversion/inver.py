from pathlib import Path
from typing import Optional

import pandas as pd

from tpwt import TPWTConfig

from .control import aftan_snr, calculate_dispersion, collect_phv_amp
from .iterate import inverse_iter, make_eqlist, make_gridnode


def tpwt_iter(config: TPWTConfig):
    """tpwt iterate, contains twice iterate.

    Parameters:
        config: tpwt config

    Examples:
        ```python
        import tpwt

        cfg = tpwt.TPWTConfig(config_toml)
        tpwt.tpwt_iter(cfg)
        ```

    Note:
        Not complete!
    """
    method = _valid_method(config.params.get("method"))
    eqlist, gridnode, stationid = _make_iter_files(config)
    binpath = config.paths.get("binpath", Path("TPWT/bin"))
    inverse_iter()


def inverse(config_toml: str):
    """tpwt inverse

    tpwt inverse, contains two steps:
        1. quanlity control
        2. tpwt iterate

    Parameters:
        config_toml: tpwt config file in toml format

    Examples:
        ```python
        import tpwt
        tpwt.inverse("config.toml")
        ```

    Note:
        Not complete!
    """
    cfg = TPWTConfig(config_toml)
    quanlity_control(cfg)
    tpwt_iter(cfg)


def quanlity_control(config: TPWTConfig):
    """tpwt quanlity control.

    Steps:
        1. calculate dispersion
        2. calculate aftan snr
        3. calculate distance
        4. calculate phase amplitude

    Parameters:
        config: tpwt config

    Examples:
        ```python
        import tpwt

        cfg = tpwt.TPWTConfig(config_toml)
        tpwt.quanlity_control(cfg)
        ```
    """
    binpath = config.paths.get("binpath", Path("TPWT/bin"))
    path_dir = Path("outputs/path")

    calculate_dispersion(
        evt_csv=str(config.paths["evt_csv"]),
        sta_csv=str(config.paths["sta_csv"]),
        path_dir=path_dir,
        binpath=binpath,
    )
    aftan_snr(sac_dir=config.paths["sac_dir"], path_dir=path_dir, binpath=binpath)

    ph_amp_dir = Path("outputs/ph_amp_dir")
    collect_phv_amp(
        config.paths["evt_csv"],
        config.paths["sta_csv"],
        config.paths["sac_dir"],
        ph_amp_dir,
        config.periods(),
        **config.params["threshold"],
        region=config.region_list(),
        ref_sta=config.model["ref_sta"],
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

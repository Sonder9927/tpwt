from pathlib import Path
from typing import Optional

import pandas as pd

from tpwt import TPWTConfig

from .filter import aftan_snr, calculate_dispersion, collect_ph_amp
from .iterate import collect_results, inverse_iter, make_pre_files


def tpwt_iter(cfg: TPWTConfig):
    """tpwt iterate, contains twice iterate.

    Steps:
        1. make iter pre files
        2. iter with 1D average phv
        3. find bad kern
        4. iter with 2D phv
        5. collect results (phv, std, eqlist)

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
    method = cfg.valid_method()
    eqlist, gridnode, stationid = make_pre_files(cfg)
    inverse_iter(method)
    collect_results(cfg.tpwt_path())


def tpwt_filter(cfg: TPWTConfig):
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
    path_dir = cfg.outpath / "path"

    dispersion_TPWT = cfg.binuse("GDM52_dispersion_TPWT")
    calculate_dispersion(
        str(cfg.paths["evt_csv"]),
        str(cfg.paths["sta_csv"]),
        path_dir,
        cfg.get_disps(),
        dispersion_TPWT,
    )
    # aftani_c_pgl_TPWT
    aftani_c_pgl_TPWT = cfg.binuse("aftani_c_pgl_TPWT")
    # spectral_snr_TPWT
    spectral_snr_TPWT = cfg.binuse("spectral_snr_TPWT")
    aftan_snr(cfg.paths["sac_dir"], path_dir, aftani_c_pgl_TPWT, spectral_snr_TPWT)

    collect_ph_amp(
        cfg.paths["evt_csv"],
        cfg.paths["sta_csv"],
        cfg.paths["sac_dir"],
        cfg.ph_path(),
        cfg.periods(),
        **cfg.params["threshold"],
        region=cfg.region.to_list(),
        ref_sta=cfg.model["ref_sta"],
    )


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
    tpwt_filter(cfg)
    tpwt_iter(cfg)

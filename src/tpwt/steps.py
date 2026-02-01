from typing import Optional

from tpwt import TPWTConfig
from tpwt import plotlib as plt
from tpwt.control import aftan_snr, calculate_dispersions, collect_ph_amp
from tpwt.inverse import collect_results, make_pre_files, tpwt_iterates


def iterative_inversion(cfg: TPWTConfig):
    """tpwt iterate, contains make pre-files and twice iterate.

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
    tpwt_iterates(method)
    collect_results(cfg.tpwt_path())


def quanlity_control(cfg: TPWTConfig):
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
    disp_model_path = cfg.paths["utils"] / "RayleighDisp.json"
    disps_path = cfg.outpath / "disps"
    calculate_dispersions(
        cfg.paths["evt_csv"], cfg.paths["sta_csv"], disp_model_path, disps_path
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


def tomography(config_toml: str, plot_figures: Optional[bool] = False):
    """tpwt

    tpwt inverse, contains two steps:
        1. quanlity control
        2. iterative inversion
        3. plot figures

    Parameters:
        config_toml: tpwt config file in toml format

    Examples:
        ```python
        import tpwt
        tpwt.tpwt("config.toml")
        ```

    Note:
        Not complete!
    """
    cfg = TPWTConfig(config_toml)
    quanlity_control(cfg)
    iterative_inversion(cfg)
    if plot_figures:
        plt.tpwt_results(cfg)

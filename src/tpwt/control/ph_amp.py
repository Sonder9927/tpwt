import pandas as pd
# from pathlib import Path


from .tpwt_gmt import gmt_surface


def collect_ph_amp(
    evt_csv,
    sta_csv,
    sac_dir,
    out_dir,
    periods,
    snr,
    dist,
    nsta,
    valid_ratio,
    tmisfit,
    ref_sta,
    region,
):
    """find phase time and amp

    Parameters:
        evt_csv: filter event record
        sta_csv: filter station record
        sac_dir: sac data
        out_dir: output path
        periods: target periods
        snr: min snr threshold
        dist: min dist threshold
        nsta: min number of stations
        valid_ratio: min ratio of valid stations
        tmisfit: max misfit between corrected and expected time
        ref_sta: reference station coordinates
        region: region for gmt surface
    """
    from tpwt._core import make_ph_amp_files

    make_ph_amp_files(
        str(evt_csv),
        str(sta_csv),
        str(sac_dir),
        str(out_dir),
        periods,
        snr,
        dist,
        nsta,
        valid_ratio,
        tmisfit,
        ref_sta,
    )

    for ph_csv in out_dir.glob("*/*ph.csv"):
        root_name = ph_csv.parent / ph_csv.stem

        df = pd.read_csv(ph_csv)

        ph_file = root_name.with_suffix(".ph.HD")
        gmt_surface(df[["lon", "lat", "time"]], region, str(ph_file))

        amp_file = root_name.with_suffix(".amp.HD")
        gmt_surface(df[["lon", "lat", "amp"]], region, str(amp_file))


# def phase_amplitude_bin(
#     periods: list[int],
#     sac_dir: Path,
#     evt_csv,
#     sta_csv,
#     out_dir: Path,
#     *,
#     snr: int,
#     tcut: int,
#     nsta: int,
#     cut_per: float,
#     dist: int,
#     region: list[float],
#     ref_sta: list[float],
#     binpath: Path,
# ):
#     from tpwt._core import make_sta_dist_file

#     # calc_distance to create sta_dist.lst
#     sta_dist = "outputs/sta_dist.lst"
#     # make_sta_dist_bin(evt_lst, sta_lst, sac_dir, sta_dist, binpath=binpath)
#     make_sta_dist_file(evt_csv, sta_csv, sac_dir, sta_dist)
#     with tqdm(total=len(periods)) as pbar:
#         for period in periods:
#             pbar.set_postfix_str(f"Processing {period=}")
#             sec_dir = _find_ph_amp_eq(period, sac_dir, snr, dist, sta_dist, binpath)
#             _correct_tt(sec_dir, period, tcut, nsta, cut_per, region, ref_sta, binpath)
#             # move preiod results
#             if out_dir:
#                 shutil.move(sec_dir, out_dir)
#             pbar.update(1)


# ###############################################################################


# def _correct_tt(sec_dir, period, tcut, nsta, cut_per, region, ref_sta, binpath):
#     correct_tt_select_data = binuse("correct_tt_select_data", binpath=binpath)
#     for ph_file in Path(sec_dir).glob("*ph.txt"):
#         with ph_file.open() as f:
#             stanum = len(f.readlines())
#         [ref_lo, ref_la] = ref_sta

#         if stanum >= nsta:
#             cmd_string = "echo shell start\n"
#             cmd_string += f"{correct_tt_select_data} "
#             cmd_string += f"{ph_file} {period} {nsta} {cut_per} "
#             cmd_string += f"{ref_lo} {ref_la} {tcut}\n"
#             cmd_string += "echo shell end"
#             subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(
#                 cmd_string.encode()
#             )
#         event_v1 = Path(f"{ph_file}_v1")
#         if event_v1.stat().st_size != 0:
#             gmt_phase_time(event_v1, region)
#             gmt_amp(event_v1, region)


# def _find_ph_amp_eq(period, sac, snr, dist, sta_dist, binpath) -> str:
#     find_phvel_amp_eq = binuse("find_phvel_amp_earthquake", binpath=binpath)
#     cmd_string = "echo shell start\n"
#     cmd_string += f"{find_phvel_amp_eq} "
#     cmd_string += f"{period} {sta_dist} {snr} {dist} {sac}/\n"
#     cmd_string += "echo shell end"
#     subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())
#     return f"{period}sac_{snr}snr_{dist}dis"

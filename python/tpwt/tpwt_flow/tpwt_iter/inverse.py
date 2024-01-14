from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
import shutil

from tpwt_p.rose import re_create_dir, remove_targets, get_dirname

from .tpwt_fns import (
    sensitivity_TPWT,
    rdsetupsimul_phamp_from_earthquake_TPWT,
    sort_files_for_iter,
    simanner_TPWT_run,
    find_bad_kern,
    simanner_and_gridgenvar,
)


def inverse_pre(param, eqlistper, node_file, staid, tpwt_dir):
    # multiprocessing
    with ProcessPoolExecutor(max_workers=5) as executor:
        for [p, v] in param.pv_pairs():
            executor.submit(
                batch_period_phampcor,
                param,
                p,
                v,
                eqlistper,
                node_file,
                staid,
                tpwt_dir,
            )


###############################################################################
def inverse_run(params, method="rswt"):
    # check if TPWT output dir exists
    if not (td := params[0].tpwt_dir).exists():
        err = f"TPWT output directory {td} is not found."
        err += "Please confirm the initilialization is successful."
        raise FileNotFoundError(err)
    if (mtd := method.lower()) == "tpwt":
        tpwt_run(params)
    elif mtd == "rswt":
        rswt_run(params)
    else:
        raise KeyError("Please choice TPWT or RSWT.")


def tpwt_run(params):
    # multiprocessing
    with ProcessPoolExecutor(max_workers=10) as executor:
        executor.map(batch_period_grid, params)


def rswt_run(params):
    # multiprocessing
    with ProcessPoolExecutor(max_workers=10) as executor:
        executor.map(batch_period_grid, params)


###############################################################################
"""
batch function
"""


def batch_period_phampcor(p, per, vel, eqlistper, nodes, staid, tpwt_dir):
    # sensitivity (this is rayleigh edition)
    smooth = p.parameter("smooth")
    damping = p.parameter("damping")
    sens_dir = p.target("sens_dir")
    all_events = p.target("all_events")
    snr = p.parameter("snr")
    nsta = p.parameter("nsta")
    dist = p.parameter("dist")

    sensitivity_TPWT(per, vel, smooth, "rayleigh", out_dir=sens_dir)

    # flag phamp
    sens_dat = Path.cwd() / sens_dir / f"sens{per}s{smooth}km.dat"
    sec_snr_dis = Path(all_events) / f"{per}sec_{snr}snr_{dist}dis"
    rdsetupsimul_phamp_from_earthquake_TPWT(
        per,
        vel,
        snr,
        dist,
        nsta,
        smooth,
        damping,
        eqlistper,
        str(sens_dat),
        str(sec_snr_dis),
    )

    # sort files and get stationid.dat
    sort_files_for_iter(per, nodes, staid, sens_dat, tpwt_dir)


def batch_period_grid(p):
    # RSWT
    per = p.per
    per_dir = p.tpwt_dir / f"per{per}"
    # will mkdir res_dir in where put result grid data
    res_dir = "rswt"
    kern = [100, 160]

    damp = str(p.damping).split(".")[1]
    avgvel1: str = first_iter_in_per_dir(
        p.per, p.smooth, damp, per_dir, res_dir, kern[0]
    )

    eqfine_to_res_dir(
        kern[0],
        per_dir / res_dir,
        per=per,
        ampcut=p.ampcut,
        tcut=p.tcut,
        stacut=p.stacut,
    )

    # go into output directory, default is new_2d
    second_iter_in_res_dir(
        kern[1],
        per,
        avgvel1,
        p.snr,
        p.dist,
        p.nsta,
        p.smooth,
        p.damping,
        damp,
        p.region,
        per_dir / res_dir,
        sec_dir=get_dirname("sec", period=per, snr=p.snr, dist=p.dist),
    )


###############################################################################


def first_iter_in_per_dir(per, smooth, damp, per_dir, res_dir, kern) -> str:
    """
    process data generated from step 4
    in TPWT_param/per
    """
    if (eq := per_dir / f"eqlistper{per}").exists():
        re_create_dir(res_dir)
    else:
        err = f"No {eq} found!"
        err += "Please confirm the initilialization is successful."
        raise FileNotFoundError(err)

    ## simannerr100 for rswt
    simanner_TPWT_run(eq, kern)

    # return avgvel and std
    vel_f = f"velarea.{per}.1.{smooth}.{damp}.sa{kern}kern"
    with open(vel_f, "r") as f:
        velarea = f.readline()

    return velarea.split()[1]


def eqfine_to_res_dir(
    kern, res_dir, *, per, ampcut, tcut, stacut, tevtrmscut=0, ampevtrmscut=0
):
    # get eqlistper.fine
    if kern == 100:
        find_bad_kern(kern, per=per, ampcut=ampcut, tcut=tcut, stacut=stacut)
    elif kern == 300:
        find_bad_kern(
            kern,
            per=per,
            ampcut=ampcut,
            tcut=tcut,
            stacut=stacut,
            tevtrmscut=tevtrmscut,
            ampevtrmscut=ampevtrmscut,
        )
    else:
        err = """
        Check the kern:\n
        100 for rswt\n
        300 for tpwt
        """
        raise KeyError(err)

    # get linenum of eqlistper.fine
    eq_fine = res_dir / r"eqlistper.fine"
    with eq_fine.open("r") as f1:
        content_list = f1.readlines()
    # update eqlistper{per}
    with open(f"{res_dir}/eqlistper{per}.update", "w+") as f2:
        for c in content_list[:-14]:
            f2.write(c)

    copy_list = ["stationid.dat", "invrsnodes"]
    for cf in copy_list:
        shutil.copy(cf, res_dir / cf)


def second_iter_in_res_dir(
    kern,
    per,
    vel,
    snr,
    dist,
    nsta,
    smooth,
    damping,
    damp,
    region,
    res_dir,
    sec_dir,
    wave_type="rayleigh",
):
    sensitivity_TPWT(per, vel, smooth, wave_type, out_dir=res_dir)

    # do rdsetupsimul phamp again
    eqlistper = res_dir / f"eqlistper{per}.update"
    sens_dat = res_dir / f"sens{per}s{smooth}km.dat"
    rdsetupsimul_phamp_from_earthquake_TPWT(
        per,
        vel,
        snr,
        dist,
        nsta,
        smooth,
        damping,
        str(eqlistper),
        str(sens_dat),
        str(sec_dir),
    )

    rm_list = [
        eqlistper,
        f"resmax{per}.dat",
        f"eqlistper.fine",
        f"phampcor.v3.{per}",
    ]
    remove_targets(rm_list)
    eqlistper = f"eqlistper{per}"
    shutil.move(f"eqlistper.v3.{per}", eqlistper)

    simanner_and_gridgenvar(kern, per, smooth, damp, region, eqlistper)

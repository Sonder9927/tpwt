import os
import shutil
import subprocess

from tpwt_p.rose import get_binuse, remove_targets
import tpwt_r


def sensitivity_TPWT(
    per, vel, smooth, wave_type="rayleigh", *, out_dir=None, bin_from="./"
):
    """
    sensitivity
    """
    # create sac
    sac_file = f"{per}.sac"
    tpwt_r.sac_sens_new_period(sac_file, per)
    # createsac_TPWT = get_binuse('createsac_TPWT', bin_from)

    # cmd_list = [
    #     f'{createsac_TPWT} <<!',
    #     f'{per}',
    #     f'{sac_file}',
    #     '!',
    # ]
    # cmd_string = '\n'.join(cmd_list)
    # subprocess.Popen(
    #     ['bash'],
    #     stdin = subprocess.PIPE
    # ).communicate(cmd_string.encode())

    # sac
    sac_cut = f"{per}.cut800t1000"
    os.putenv("SAC_DISPLAY_COPYRIGHT", "0")
    s_list = [
        "wild echo off",
        "cut 750 1050",
        f"r {sac_file}",
        "taper w 0.1666667",
        f"w {sac_cut}",
        "cuterr fillz",
        "cut 0 2000",
        f"r {sac_cut}",
        "cuterr u",
        f"w {sac_cut}",
        "fft",
        "wsp",
        "q\n",
    ]
    s = "\n".join(s_list)
    subprocess.Popen(["sac"], stdin=subprocess.PIPE).communicate(s.encode())

    # getdatafromsac_GZ
    input = f"{sac_cut}.am"
    # output = input + '.dat'
    # getdatafromsac = get_binuse('getdatafromsac_GZ', bin_from)

    # cmd_list = [
    #     f'{getdatafromsac} <<!',
    #     f'{input}',
    #     f'{output}',
    #     '!',
    # ]
    # cmd_string = '\n'.join(cmd_list)
    # subprocess.Popen(
    #     ['bash'],
    #     stdin = subprocess.PIPE
    # ).communicate(cmd_string.encode())

    # # sensitivity_wavetype
    # sen_input = output
    sen_output = f"sens{per}s{smooth}km.dat"
    tpwt_r.sac_sens(input, vel, smooth, sen_output)
    # sensitivity = get_binuse(f'sensitivity_{wave_type}', bin_from)

    # cmd_list = [
    #     f'{sensitivity} <<!',
    #     f'{vel}',
    #     f'{sen_input}',
    #     f'{sen_output}',
    #     f'{smooth}',
    #     '!',
    #     f'rm {per}.*',
    # ]
    # cmd_string = '\n'.join(cmd_list)
    # subprocess.Popen(
    #     ['bash'],
    #     stdin = subprocess.PIPE
    # ).communicate(cmd_string.encode())

    if out_dir:
        # check if des_dir exists
        if os.path.exists(out_dir):
            shutil.move(sen_output, out_dir)
        else:
            err_description = f"Output dir {out_dir} is not found."
            err_description += "Please check the target directory."
            raise Exception(err_description)


###############################################################################


def write_period_eqlistper_temp(
    per,
    vel,
    snr,
    dist,
    nsta,
    smooth,
    damping,
    eqlistper,
    temp,
    sens_dat: str,
    sec_snr_dis: str,
):
    """
    write eqlistper temp for rdsetupsimul_phamp in each period
    """
    shutil.copyfile(eqlistper, temp)
    damp = str(damping).split(".")[1]
    # write new content
    c_list = [
        "1",
        f"{1 / per}",
        f"detail.{per}.1.{smooth}.{damp}",
        f"summar.{per}.1.{smooth}.{damp}",
        "invrsnodes",
        f"phampcor.{per}",
        f"covar.{per}.1.{smooth}.{damp}",
        f"mavamp.{per}.1.{smooth}.{damp}",
        f"resmax{per}.dat",
        f"velarea.{per}.1.{smooth}.{damp}",
        f"5 {smooth} {damping} {damping}",
        f"{vel}",
        sens_dat,
        sec_snr_dis,
        f"{snr} {dist} {nsta}",
    ]
    content = "\n".join(c_list)
    with open(temp, "a") as f:
        f.write(content)


def rdsetupsimul_phamp_from_earthquake_TPWT(
    per,
    vel,
    snr,
    dist,
    nsta,
    smooth,
    damping,
    eqlistper: str,
    sens_dat: str,
    sec_snr_dis: str,
    bin_from="./",
):
    """
    rdsetupsimul phamp
    """
    # write temp file
    temp = f"eqlistper{per}.tp"

    write_period_eqlistper_temp(
        per,
        vel,
        snr,
        dist,
        nsta,
        smooth,
        damping,
        eqlistper,
        temp,
        sens_dat,
        sec_snr_dis,
    )

    # rdsetupsimul_phamp_from_earthquake
    rdsetupsimul_phamp = get_binuse(
        "rdsetupsimul_phamp_from_earthquake", bin_from=bin_from
    )

    c_list = [
        f"{rdsetupsimul_phamp}",
        f"{temp} eqlistper.v3.{per} phampcor.v3.{per}",
    ]
    c_string = " ".join(c_list)  # kong ge qu fen kai mingling he can shu
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(c_string.encode())

    remove_targets([temp])


###############################################################################
def sort_files_for_iter(per, nodes, staid, sens_dat, out_dir):
    per_dir = out_dir / f"per{per}"
    per_dir.mkdir()
    shutil.move(f"phampcor.{per}", per_dir)
    shutil.move(f"eqlistper.v3.{per}", per_dir / f"eqlistper{per}")
    shutil.copyfile(nodes, per_dir / nodes)
    shutil.copyfile(sens_dat, per_dir / sens_dat.name)
    shutil.copyfile(staid, per_dir / staid)

    remove_targets([f"resmax{per}.dat", f"phampcor.v3.{per}"])


###############################################################################


def simanner_TPWT_run(eqlistper, kern, bin_from="./"):
    """
    simanner with the kern
    """
    simanner = get_binuse(f"simannerr{kern}.kern", bin_from=bin_from)
    c_string = f"{simanner} < {eqlistper}"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(c_string.encode())


def find_bad_kern(
    kern,
    *,
    per,
    ampcut,
    tcut,
    stacut,
    tevtrmscut=None,
    ampevtrmscut=None,
    bin_from="./",
):
    """
    find bad kern 100 or 300
    will create eqlistper.fine
    """
    fn = get_binuse(f"find_bad_kern{kern}", bin_from=bin_from)
    c_string = f"{fn} "
    if kern == 300:
        c_string += f"{ampcut} {tcut} {stacut} {tevtrmscut} {ampevtrmscut} "
        c_string += f"eqlistper{per} eqlistper.v1.{per}"
    elif kern == 100:
        c_string += f"{ampcut} {tcut} {stacut} eqlistper{per}"
    else:
        raise KeyError("Please chose kern between 100 and 300.")

    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(c_string.encode())


def simanner_and_gridgenvar(kern, per, smooth, damp, region, eq, bin_from="./"):
    """
    second time simanner with kern 160 or 360
    and generate grid finally
    """
    simanner_TPWT_run(kern, eq, bin_from=bin_from)

    f_in = f"velgridinp.{per}.1.{smooth}.{damp}.sa{kern}kern"
    grid_file = f"grid.{per}.{kern}.{smooth}.{damp}.{smooth}"
    # write the content of temp file
    c_list = [
        "1",
        "0",
        f".125 {smooth}",
        "invrsnodes",
        " ".join(region),
        grid_file,
        f"covar.{per}.1.{smooth}.{damp}.sa{kern}kern",
        f"stddev.{per}.{kern}.{smooth}.{damp}.{smooth}",
    ]
    content = "\n".join(c_list)
    with open(f_in, "w+") as f:
        f.write(content)
        f.write("\n")
        with open(f"velarea.{per}.1.{smooth}.{damp}.sa{kern}kern", "r") as v:
            shutil.copyfileobj(v, f)

    # create grid
    gridgenvar = get_binuse("gridgenvar.yang_v2", bin_from=bin_from)
    c_string = f"{gridgenvar} < {f_in}"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(c_string.encode())

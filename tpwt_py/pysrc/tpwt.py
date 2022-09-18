from icecream import ic
import numpy as np
import pandas as pd
import pathlib, os
import shutil
import pygmt
import subprocess

"""
EXPORT
"""

# get bin for using
def get_binuse(b: str, bin_from='./'):
    return pathlib.Path(bin_from) / 'TPWT/bin' / b

# mk_pathfile_TPWT
def mk_pathfile_TPWT(sta1, sta2, pathfile):
    """
    mk_pathfile makes file pathfile
    format: n1 n2 sta1 sta2 xlat1 xlon1 xlat2 xlon2
    """


# file generator in a list
def f_generator(end, dir='./'):
    """
    a generator for sac files list in one event dir.
    """
    for sacfile in os.listdir(dir):
        if sacfile.endswith(end):
            yield sacfile


# plot phase time
def plot_phase_time(input_map: str, area: dict):
    region = f'{area["west"]}/{area["east"]}/{area["sourth"]}/{area["north"]}'
    grid = pygmt.surface(
        data = input_map,
        spacing = .2,
        region = region,
    )
    pygmt.grd2xyz(
        grid = grid,
        region = region,
        output_type = "file",
        outfile = input_map + ".HD",
    )


# plot amp
def plot_amp(input_map, area):
    parts = input_map.split(".")
    parts[1] = "_am."
    output_am = ''.join(parts)

    out_file = pd.read_csv(
        input_map,
        sep='\s+',
        usecols=[0, 1, 4],
        engine='python'
    )
    out_file.to_csv(output_am, sep=' ', header=False, index=False)

    region = [area[i] for i in ['west', 'east', 'sourth', 'north']]
    grid = pygmt.surface(
        data = output_am,
        spacing = .2,
        region = region,
    )
    pygmt.grd2xyz(
        grid = grid,
        region = region,
        output_type = "file",
        outfile = output_am + ".HD",
    )


# expand region
def area_expanded(area: dict, value: float) -> dict:
    area['east'] += value
    area['west'] -= value
    area['sourth'] -= value
    area['north'] += value
    return area

# create inversion grid nodes
def creatgridnode_TPWT(out_file: str, area: dict, dgrid: list):
    """
    get inversion grid nodes
    """


def get_per_vel_dicts(period: list, vel: list) -> list:
    if len(period) == len(vel):
        return [{'period': period[n], 'vel': vel[n]} for n in range(len(period))]
    else:
        raise Exception('#periods != #vels, please check parameters lists.')


def sensitivity_TPWT(p, wave_type, *, out_dir=None, bin_from='./'):
    # create sac
    # sac
    # getdatafromsac_GZ
    # sensitivity_wavetype
    if out_dir:
        # check if des_dir exists
        if os.path.exists(out_dir):
            shutil.move(sen_output, out_dir)
        else:
            err_description = f'Output dir {out_dir} is not found.'
            err_description += 'Please check the target directory.'
            raise Exception(err_description)


def get_TPWT_output_dir(snr, tcut, smooth, damping) -> str:
    return f'TPWT_{snr}snr_{tcut}t_{smooth}smooth_{damping}damping'


def write_period_eqlistper_temp(p, eqlistper, temp, sens_dat: str, sec_snr_dis: str):
    """
    write new content
    """


def rdsetupsimul_phamp_from_earthquake_TPWT(param, eqlistper, sens_dat: str, sec_snr_dis: str, bin_from='./'):
    """
    write temp file
    rdsetupsimul_phamp_from_earthquake
    """


def simanner_TPWT_run(kern, eqlistper, bin_from='./'):
    """
    simanner using eqlistper and input kern
    """


def simanner160_and_gridgenvar(p, eq, bin_from):
    simanner_TPWT_run(160, eq, bin_from=bin_from)
    """
    simanner with 160 kern and gridgenvar
    """
    # write the content of temp file
    # create grid

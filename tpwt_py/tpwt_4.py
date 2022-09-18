from icecream import ic
from multiprocessing import Process
import pandas as pd
import os, pathlib, shutil

# My scripts
# functions
from pysrc.get_param import get_param_json
from pysrc.tpwt import (
    area_expanded,
    creatgridnode_TPWT,
    get_per_vel_dicts,
    sensitivity_TPWT,
    get_TPWT_output_dir,
    rdsetupsimul_phamp_from_earthquake_TPWT,
)

# classes
from pysrc.get_param import Param

"""
04
"""

def create_invrsnodes(outfile, sta, region, dlat, *dlon):
    if os.path.exists(sta):
        area = area_expanded(region, .5)
        dlon = dlon or dlat
        creatgridnode_TPWT(outfile, area, [dlat, dlon])

    else:
        raise Exception('No station.lst found.')


##############################################################################


def get_stationid_and_sort_files(p, sens_dat, out_dir):
    per = p.period
    per_dir = out_dir / f'{per}'
    os.mkdir(per_dir)
    shutil.move(f'phampcor.{per}', per_dir)
    shutil.move(f'eqlistper.v3.{per}', per_dir/f'eqlistper{per}')
    shutil.copyfile(p.invrsnodes, per_dir/p.invrsnodes)
    shutil.copyfile(sens_dat, per_dir/os.path.basename(sens_dat))
    rm_list =[
        f'resmax{per}.dat',
        f'phampcor.v3.{per}',
    ]
    for rm_file in rm_list:
        os.remove(rm_file)

    # stationid
    stationid_dat = 'stationid.dat'
    staid = pd.read_csv(
        p.sta,
        sep = '\s+',
        usecols = [0],
        names = ['sta'],
        engine ='python'
    )
    staid.insert(loc=1, column='NR1', value=[i for i in range(1, len(staid)+1)])
    staid.insert(loc=2, column='NR2', value=[i for i in range(1, len(staid)+1)])
    staid.to_csv(per_dir/stationid_dat, sep=' ', header=False, index=False)


def process_period_phampcor(param, out_TPWT, wave_type):
    # sensitivity (this is rayleigh version)
    sensitivity_TPWT(param, wave_type, out_dir=param.sens)

    # flag phamp
    eqlistper = f'{param.sac}/eqlistper'
    sens_dat = str(pathlib.Path.cwd() / param.sens / f"sens{param.period}s{param.smooth}km.dat")
    sec_snr_dis = str(pathlib.Path(param.all_events) / f"{param.period}sec_{param.snr}snr_{param.dist}dis")
    rdsetupsimul_phamp_from_earthquake_TPWT(param, eqlistper, sens_dat, sec_snr_dis)

    # sort files and get stationid.dat
    get_stationid_and_sort_files(param, sens_dat, out_TPWT)

    ic("period", param.period, "done")


def process_periods_phampcor(param, per_vel_dicts):
    # check if 'all_events' exists
    if not os.path.exists(check_dir := param.all_events):
        err_description = f'No {check_dir} found.'
        err_description += 'Please make sure tpwt step 2 is done.'
        raise Exception(err_description)

    # get TPWT output dir and clean the created before
    out_TPWT = get_TPWT_output_dir(param.snr, param.tcut, param.smooth, param.damping)
    out_TPWT = pathlib.Path(out_TPWT)
    for out in [out_TPWT, param.sens]:
        if os.path.exists(out):
            shutil.rmtree(out)
        os.mkdir(out)

    # wave type: rayleigh or love
    # (this version only support rayleigh)
    wave_type = ['rayleigh', 'love']
    # process every period
    process_list = []
    for per_vel in per_vel_dicts:
        param.period = per_vel['period']
        param.vel = per_vel['vel']
        p = Process(target=process_period_phampcor,
                   args=[param, out_TPWT, wave_type[0]])
        process_list.append(p)
        p.start()

    for p in process_list:
        p.join()

    # mark finish
    pathlib.Path('flag_phampcor').touch()
    ic("Flag phampcor done.")


def tpwt_04(param_json, *, snr=None, tcut=None, smooth=None, damping=None):
    # instancs a parameters class
    p4 = Param
    # get parameters
    param = get_param_json(param_json)
    # variables
    p_var = param['variables']
    p4.snr = snr or p_var['snr'][0]
    p4.tcut = tcut or p_var['tcutoff'][0]
    p4.smooth = smooth or p_var['smooth'][0]
    p4.damping = damping or p_var['damping'][0]
    p4.damp = str(p4.damping).split('.')[1]
    # files
    p_f = param['files']
    p4.sta = p_f["sta"]
    p4.sac = p_f['sac']
    p4.sens = p_f['sens']
    p4.all_events = p_f['all_events']
    # immutables
    p_immu = param['immutables']
    p4.dist = p_immu['dist']
    p4.nsta = p_immu['nsta_cutoff']
    p4.region = p_immu['region']
    # p4.period = p_immu['period']
    # p4.avgvel = p_immu['average_velocity']

    # belong to tpwt4
    # inversion grid nodes file
    p4.invrsnodes = 'invrsnodes'
    dgrid = .5

    # flag_sta_dist
    if os.path.exists('flag_phampcor'):
        ic('The flag_phampcor existed, will skip running this part.')
    else:
        if os.path.exists(invrsnodes:=p4.invrsnodes):
            ic('The invrsnodes existed, will not re-create it.')
        else:
            create_invrsnodes(invrsnodes, p4.sta, p4.region, dgrid)
        
        per_vel_dicts: list = get_per_vel_dicts(p_immu['period'], p_immu['average_velocity'])
        # process_periods_phampcor(p4, per_vel_dicts)
        process_periods_phampcor(p4, [per_vel_dicts[2]])

        # rm invrsnodes in vaulty
        os.remove(invrsnodes)
    
    ic("TPWT step 4 done")


if __name__ == "__main__":
    tpwt_04("param.json", snr=15, tcut=10, smooth=65, damping=.25)

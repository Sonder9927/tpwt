"""
There are functions of tpwt flow.

Example:
    from tpwt import tpwt_run

    tpwt_run("param.jsonc")
"""


from icecream import ic
from tpwt import rs, tpwt_flow


def evt_files(param) -> None:
    """make event files
    make `event.cat` for mktraceiodb
    make `event.csv` for tpwt_run

    Args:
        param (Param): param for tpwt program
    Returns:
        None
    """
    evt = tpwt_flow.EvtMaker(
        param.target("evt30"), param.target("evt120"), param.parameter("timedelta")
    )
    # event.cat for
    cat_form = "%Y/%m/%d,%H:%M:%S"
    evt_cat = evt.extract(cat_form, cols=["time"])
    evt_cat.to_csv(param.target("evt_cat"), sep=" ", index=False, header=False)
    lst_form = "%Y%m%d%H%M"
    evt_lst = evt.extract(lst_form)
    evt_lst.to_csv(param.target("evt_csv"), index=False)


def evt_cut(param):
    data = tpwt_flow.Evt_Cut(
        param.target("og_data")
    )  # if set z_pattern to '1' the new file will be `file_1`
    data.cut_event(
        param.target("cut_dir"),
        param.target("evt_cat"),
        param.parameter("time_delta"),
    )  # if cut_from: use cut_from else: use self.only_Z_1Hz


def sac_format(param):
    """format sac files
    Args:
        param (Param): param for tpwt program
    Returns:
        None
    """
    fmt = tpwt_flow.SacFormatter()
    fmt.format(
        param.target("sac"), evt=param.target("evt_csv"), sta=param.target("sta_csv")
    )


def old_sac_format(param):
    sac = tpwt_flow.SacFormater(
        param.target("cut_dir"),
        evt=param.target("evt_csv"),
        sta=param.target("sta_csv"),
    )
    sac.format(param.target("sac"))
    sac.filter_events(param.target("sac"), param.target("evt_lst"))


def tpwt_check(data: str):
    t = Check_In(data)
    message = t.check_form()
    ic(message)


def quanlity_control(param):
    # data = tpwt_flow.Data_Filter(bp, param.model["periods"])
    data = tpwt_flow.Data_Filter(param)
    data.filter()


def tpwt_iter(param):
    tpwt = tpwt_flow.TPWT_Iter(param)
    tpwt.iter()


def mcmc(param):
    periods = [
        8, 10, 12, 14, 16, 18,
        20, 25, 30, 35, 40, 45, 50,
        60, 70, 80, 90, 100, 111, 125, 143,
    ]  # fmt: skip
    mc = tpwt_flow.MCMC(param)
    mc.mc_init("TPWT/utils/moho.lst", periods)  # , clip=True)


def tpwt_run(param_json: str) -> None:
    """tpwt flow
    This function run all steps of tpwt flow.

    Args:
        param_json (str): param in json file

    Tips:
        `jsonc` file is also OK.

    Steps:
        1. evt_files: make event files
        2. evt_cut: cut events
        3. sac_format: format sac data
        4. tpwt_check: check input
        5. quanlity_control filter data
        6. tpwt_iter tpwt
        7. mcmc collect grids for mcmc
    """
    # start
    # get parameters
    param = rs.load_param(param_json)

    # get event lst and cat from 30 to 120
    evt_files(param)

    # data cut event
    evt_cut(param)

    # process sac files
    sac_format(param)

    # check data format
    tpwt_check(param.target("sac"))

    # mass control
    quanlity_control(param)

    # tpwt
    tpwt_iter(param)

    # mc
    mcmc(param)


if __name__ == "__main__":
    tpwt_run("param.jsonc")

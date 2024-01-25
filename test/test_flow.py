from tpwt.tpwt_flow import SacFormatter
from tpwt import evt_files
from tpwt import rs


def test_evt_files(param):
    evt_files(param)


def test_head1(param):
    """
    test extract and format
    """
    fmt = SacFormatter()
    fmt.format(dir="../sac", evf=param.target("evt_csv"), stf=param.target("sta_csv"))


if __name__ == "__main__":
    param = rs.load_param("param.jsonc")
    # test_evt_files(param)
    test_head1(param)

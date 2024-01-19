from tpwt import evt_files, sac_format, head_from_sac
from tpwt import rs


def test_evt_files(param):
    evt_files(param)

def test_head1(param):
    """
    test extract and format
    """
    head_from_sac(param.target("sac"))
    sac_format(param)


if __name__ == "__main__":
    param = rs.load_param("param.jsonc")
    # test_evt_files(param)
    test_head1(param)

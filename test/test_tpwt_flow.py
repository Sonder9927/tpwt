from tpwt import evt_files
from tpwt import rs


def test_evt_files(param):
    evt_files(param)


if __name__ == "__main__":
    param = rs.load_param("param.jsonc")
    test_evt_files(param)

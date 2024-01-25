from tpwt import Checker


def test_check():
    checker = Checker()
    checker.check_lst("sac", evf="data/txt/event.csv", stf="data/txt/station.csv")
    checker.check_heads("sac")
    checker.log_info()


if __name__ == "__main__":
    test_check()

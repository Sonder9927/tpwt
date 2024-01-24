from tpwt import Checker


def test_check():
    checker = Checker()
    checker.check_heads("sac")
    # checker.check_lst("sac", evt_lst="event.lst",sta_lst="station.lst")


if __name__ == "__main__":
    test_check()

from tpwt import Checker


def test_check():
    checker = Checker()
    checker.check_heads("../classfied_events")
    checker.check_lst("../classfied_events", evt_lst="event.lst",sta_lst="station.lst")


if __name__ == "__main__":
    test_check()

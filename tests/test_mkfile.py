import tpwt


def test_gen_pred_files():
    tpwt.libtpwt.make_pred_files(
        "tests/outputs/GDM52_dispersion.out", "tests/outputs/lpath"
    )


def test_gen_pathfile():
    tpwt.libtpwt.make_pathfile(
        "tests/data/event.csv", "tests/data/station.csv", "tests/pathfile"
    )


if __name__ == "__main__":
    print(tpwt.libtpwt.hello_from_rust())
    # test_gen_pathfile()
    test_gen_pred_files()

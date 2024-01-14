from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import shutil


def tpwt_grids_collect(tpwt_path: Path, grids_path: Path):
    grid_files = tpwt_path.glob("*/*/grid*")
    check_files = tpwt_path.glob("*/*/*/grid*")
    with ThreadPoolExecutor(max_workers=10) as executor:
        for f in grid_files:
            executor.submit(collect_gird_file, f, grids_path)
        for f in check_files:
            executor.submit(collect_gird_file, f, grids_path, "_check")


def collect_gird_file(f: Path, gp: Path, check=""):
    if f.suffix != ".ave":
        per = f.parents[-2]
        fnew = gp / "tpwt_grids" / f"tpwt{check}_{per}"
        shutil.copy(f, fnew)

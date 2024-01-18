from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
# import obspy

from tpwt.rose import glob_patterns


class Check_In:
    def __init__(self, data) -> None:
        self.data = Path(data)

    def check_form(self):
        targets = glob_patterns("rglob", self.data, ["*.sac"])

        with ThreadPoolExecutor(max_workers=10) as pool:
            ts = []
            for target in targets:
                t = pool.submit(batch_check, target)
                ts.append(t)

            for t in ts:
                if t.result():
                    for i in reversed(ts):
                        i.cancel()
                    return "Sucessfully found valid input files."

        return "No useful file found."


def batch_check(target: Path) -> bool:
    st = obspy.read(target)
    tr = st[0]

    try:
        dist = tr.stats.sac["dist"]
    except KeyError:
        dist = False

    conditions = [
        len(target.parent.name) == 12,
        len(target.name.split(".")[0]) == 12,
        dist,
    ]

    return all(conditions)

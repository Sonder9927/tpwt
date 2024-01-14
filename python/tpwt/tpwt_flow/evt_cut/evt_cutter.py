from concurrent.futures import ProcessPoolExecutor
from pathlib import Path
from icecream import ic
import os, subprocess

from tpwt_p import rose


class Evt_Cut:
    def __init__(self, data: str) -> None:
        self.data = Path(data)
        self.patterns = ["*.sac", "*.SAC"]
        ic("Hello, this is EVT cutter.")

    def cut_event(self, target, cat, time_delta):
        """
        cut event from data using event.cat
        and result is in cut_dir
        """
        ic("getting cutted events...")

        self.target = rose.re_create_dir(target)

        # get binary program
        mktraceiodb = rose.get_binuse("mktraceiodb")
        cutevent = rose.get_binuse("cutevent")

        # get list of mseed/SAC files (direcroty and file names)
        sacs = rose.glob_patterns("rglob", self.data, self.patterns)
        # batch process
        batch = 1_000
        sacs_batch_list = [sacs[i : i + batch] for i in range(0, len(sacs), batch)]
        with ProcessPoolExecutor(max_workers=5) as executor:
            for i, s in enumerate(sacs_batch_list):
                executor.submit(
                    batch_cut_event,
                    i + 1,
                    s,
                    mktraceiodb,
                    cutevent,
                    cat,
                    time_delta,
                    self.target,
                )


# batch function
###############################################################################


def batch_cut_event(id, sacs, mktraceiodb, cutevent, cat, time_delta, target):
    """
    batch function for cut_event
    """
    lst = f"data_z.lst_{id}"
    db = f"data_z.db_{id}"
    done_lst = f"done_z.lst_{id}"

    with open(lst, "w+") as f:
        for sac in sacs:
            f.write(f"{sac}\n")

    ic(id)
    cmd_string = "echo shell start\n"
    cmd_string += (
        f"{mktraceiodb} -L {done_lst} -O {db} -LIST {lst} -V\n"  # no space at end!
    )
    cmd_string += f"{cutevent} "
    cmd_string += f"-V -ctlg {cat} -tbl {db} -b +0 -e +{time_delta} -out {target}\n"
    cmd_string += "echo shell end"
    subprocess.Popen(["bash"], stdin=subprocess.PIPE).communicate(cmd_string.encode())

    rose.remove_targets([lst, db, done_lst])


###############################################################################

# def decimate_obspy(ffrom, fto: str):
#     # method by obspy
#     # Read the seismogram.
#     st = obspy.read(ffrom)
#     # There is only one trace in Stream object.
#     tr = st[0]
#     # Decimate 5Hz by a factor of 5 to 1Hz.
#     # Note that this automatically includes a lowpass filtering with corner frequency 20Hz.
#     tr_new = tr.copy()
#     tr_new.decimate(factor=5, strict_length=False)
#     # Save the new data.
#     tr_new.write(fto, format="SAC")

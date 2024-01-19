import obspy


class Obs:
    def __init__(self, target, evt, sta, channel: str) -> None:
        self.evt = evt
        self.sta = sta
        self.channel = channel
        self.target = target
        st = obspy.read(self.target)
        tr = st[0]
        self.tr = tr.copy()

    def ch_obs(self):
        # change event info
        self.tr.stats.sac["evla"] = self.evt.la
        self.tr.stats.sac["evlo"] = self.evt.lo
        # self.tr.stats.sac["evdp"] = self.evt.dp  # optional, not ready to get `dp` with the Point class defined in rust

        self.tr.stats.sac["stla"] = self.sta.la
        self.tr.stats.sac["stlo"] = self.sta.lo
        # self.tr.stats.sac["stel"] = self.sta.dp  # optional

        # change channel
        self.tr.stats.channel = self.channel

        self.tr.write(str(self.target), format="SAC")

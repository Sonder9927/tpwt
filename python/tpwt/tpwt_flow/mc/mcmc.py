from .grid_data import mkdir_grids_path


class MCMC:
    def __init__(self, param) -> None:
        self.grids = param.target("grids")
        self.mcmc = param.target("mcmc")
        self.sta_file = param.target("sta_lst")
        self.region = param.region().to_list()

    def mc_init(self, moho_file, periods, clip=False):
        sta_file = self.sta_file if clip else None
        mkdir_grids_path(
            self.grids,
            self.mcmc,
            region=self.region,
            moho_file=moho_file,
            periods=periods,
            sta_file=sta_file,
        )

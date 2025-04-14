import tpwt


def main():
    cfg = tpwt.ConfigLoader("config.toml")
    # cfg.make_hull_files()
    plt = tpwt.Ploter(cfg)
    # plt.plot_region()
    # plt.plot_phase_velocities(clip=True)
    for per in [50, 60, 80, 100]:
        plt.plot_phase_velocity(per, clip=True, phv_csv="data/txt/phv.csv")
    # plt.plot_diff(period=60, csvf="data/txt/aswms_phv.csv", clip=True, ave=True)


if __name__ == "__main__":
    main()

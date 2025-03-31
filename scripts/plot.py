import tpwt


def main():
    cfg = tpwt.ConfigLoader("config.toml")
    # cfg.make_hull_files()
    plt = tpwt.Ploter(cfg)
    # plt.plot_region()
    # plt.plot_phase_velocities(clip=True)
    for per in [20, 25, 30, 40, 50, 60, 70, 80, 90, 100, 120, 140]:
        plt.plot_phase_velocity(per, clip=True, phv_csv="data/txt/aswms_phv.csv")


if __name__ == "__main__":
    main()

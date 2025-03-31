import tpwt


def main():
    cfg = tpwt.ConfigLoader("config.toml")
    plt = tpwt.Ploter(cfg)
    plt.plot_region()


if __name__ == "__main__":
    main()

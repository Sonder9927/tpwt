from tpwt import rs
from icecream import ic


def main():
    param = rs.load_param("param.jsonc")
    ic(param.target("sac"))


if __name__ == "__main__":
    main()

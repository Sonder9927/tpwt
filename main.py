from tpwt import load_param
from icecream import ic


def main():
    param = load_param("param.json")
    ic(param.target("sac"))


if __name__ == "__main__":
    main()

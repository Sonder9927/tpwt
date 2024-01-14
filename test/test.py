from tpwt import load_param
from icecream import ic


def main(param_json: str):
    param = load_param(param_json)
    ic(param.target("path"))


if __name__ == "__main__":
    main("param.json")

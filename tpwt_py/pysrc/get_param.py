import demjson

# param class
class Param:

    def __repr__():
        return "This is a parameters class."


# json
def get_param_json(json_file):
    """
    Get parameters from json data file.
    """
    return demjson.decode_file(json_file)


if __name__ == "__main__":
    print(get_param_json("param.json"))

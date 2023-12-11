from attrs import define
import os
import yaml

save_file = os.path.expanduser("~/.config/i3/i3-launcher.yaml")


# FIXME not used yet
def expand(path):
    if path is None:
        return None

    if type(path) is list:
        return [os.path.expanduser(os.path.expandvars(x)) for x in path]

    elif type(path) is str:
        return " ".join(expand(path.split(" ")))

    else:
        return os.path.expanduser(os.path.expandvars(path))


def load_config():
    """
    Loads the i3-launcher config from the config file, if it exists.
    """
    try:
        with open(save_file, "r") as f:
            return yaml.safe_load(f)

    except FileNotFoundError:
        return {}  # ignore and use empty dict


def save_config(save_tree):
    """
    Saves the i3-launcher config from the config file, if it exists.

    If the file is missing, an empty dict is returned.
    """
    with open(save_file, "w") as f:
        yaml.dump(save_tree, f)

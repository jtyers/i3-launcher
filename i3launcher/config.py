from __future__ import annotations

from attrs import define
from cattrs import Converter
from enum import Enum
from typing import Optional
import os
import yaml

save_file = os.path.expanduser("~/.config/i3/i3-launcher.yaml")
converter = Converter(forbid_extra_keys=True, omit_if_default=True)


class SplitDirection(str, Enum):
    HORIZONTAL = "horizontal"
    VERTICAL = "vertical"


@define
class Config:
    workspaces: list[Workspace] = []

    def get_workspace(self, name: str) -> Optional[Workspace]:
        for w in self.workspaces:
            if w.name == name:
                return w

        return None


@define
class Workspace:
    name: str
    on_start_exec: Optional[list[str]] = None
    split: Optional[SplitDirection] = None


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


def load_config() -> Config:
    """
    Loads the i3-launcher config from the config file, or a blank one if it doesn't exist.
    """
    try:
        with open(save_file, "r") as f:
            return converter.structure(yaml.safe_load(f), Config)

    except FileNotFoundError:
        return Config()


def save_config(config: Config) -> None:
    """
    Saves the i3-launcher config to the config file.
    """
    with open(save_file, "w") as f:
        yaml.dump(converter.unstructure(config), f)

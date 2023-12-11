#!/usr/bin/env python3

# usage: i3-save <workspace name>

import click
import i3ipc

from i3launcher.config import load_config
from i3launcher.i3 import launch_workspace
from i3launcher.i3 import save_workspace_state_to_config

connection = i3ipc.Connection()


@click.group()
def main():
    ...


@main.command("load")
@click.argument("workspace_name")
def load(workspace_name):
    save_tree = load_config()
    launch_workspace(
        connection, save_tree, workspace_name, launch_type="executeOnStart"
    )


@click.option(
    "--target",
    type=click.Choice(["all", "current"]),
    default="all",
    help="Specify which workspaces to save",
)
@main.command("save")
def save(target: str):
    save_workspace_state_to_config(connection, all_workspaces=(target == "all"))


if __name__ == "__main__":
    main()

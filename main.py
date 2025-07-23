#!/usr/bin/env python3

# usage: i3-save <workspace name>

import click
import i3ipc
import inject

from i3launcher.config import load_config, Config
from i3launcher.injector import configure_injector
from i3launcher.i3 import I3Launcher


@click.group()
def main():
    config = load_config()
    connection = i3ipc.Connection()

    configure_injector(config, connection)


@main.command("launch-all")
def launch_all():
    l = I3Launcher()
    l.launch_all_workspaces()


@main.command("launch")
@click.argument("workspace_name")
def launch(workspace_name):
    l = I3Launcher()
    l.launch_workspace(workspace_name)


@main.command("list")
def list_workspaces():
    config = inject.instance(Config)
    if not config.workspaces:
        click.echo("No workspaces configured.")
        return
    
    for workspace in config.workspaces:
        click.echo(workspace.name)


@click.option(
    "--target",
    type=click.Choice(["all", "current"]),
    default="all",
    help="Specify which workspaces to save",
)
@main.command("save")
def save(target: str):
    l = I3Launcher()
    l.save_workspace(all_workspaces=(target == "all"))


if __name__ == "__main__":
    main()

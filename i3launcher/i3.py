import i3ipc
import re
import subprocess

from .config import load_config
from .config import save_config


def launch_workspace(
    connection, save_tree, workspace_name, launch_type="executeOnStart", rename=True
):
    """
    Given a save_tree, launch and execute the start or finish
    commands associated with a particular workspace name.
    """

    # strip any leading numbers from the workspace name; so
    # "3:www", "3 www", "3_www" and "3-www" all become "www"
    workspace_name = re.sub(r"^\d\s*[:\s_\-]\s*", "", workspace_name)
    print("launch_workspace", workspace_name, launch_type)

    if save_tree.get(workspace_name):
        if save_tree[workspace_name].get(launch_type):
            for cmd in save_tree[workspace_name][launch_type]:
                # run in connection context, since evt.old is actually gone
                print("about to execute", cmd)
                connection.command("exec " + cmd)

    if rename:
        workspace = connection.get_tree().find_focused().workspace()
        connection.command(
            'rename workspace to "' + str(workspace.num) + " " + workspace_name + '"'
        )


def save_workspace_state_to_config(connection, all_workspaces: bool = False):
    """
    Save the currently running windows in the workspace with the given name
    to i3-launcher's config file. We do this by grabbing the matching workspace,
    finding each window and then finding the _NET_WM_PID, which tells us
    the PID that started that window, and then getting the full command
    for that PID.

    If all_workspaces is omitted, the currently focussed workspace is
    assumed.
    """
    save_tree = {}

    try:
        save_tree = load_config()

    except FileNotFoundError:
        pass  # ignore and use empty dict

    tree = connection.get_tree()
    target_workspaces: list[i3ipc.Con] = []

    if all_workspaces:
        target_workspaces = list(tree.workspaces())

    else:
        # if no workspace provided, use the currently focussed one
        focused_window = connection.get_tree().find_focused()
        target_workspaces = [focused_window.workspace()]

    if not target_workspaces:
        raise ValueError("no workspaces found")

    for target_workspace in target_workspaces:
        # as usual, strip leading numbers from the workspace name
        workspace_name = re.sub(r"^\d\s*[:\s_\-]\s*", "", target_workspace.name)
        workspace_save_tree = save_tree.get(workspace_name)

        if not workspace_save_tree:
            workspace_save_tree = {}
            save_tree[workspace_name] = workspace_save_tree

        # note that we overwrite executeOnStart here, in all cases
        executeOnStart: list[str] = []
        workspace_save_tree["executeOnStart"] = executeOnStart

        for window in target_workspace.leaves():
            window_pid_xprop = subprocess.run(
                ["xprop", "-id", hex(window.window), "_NET_WM_PID"], capture_output=True
            )
            window_pid = window_pid_xprop.stdout.strip().decode()
            window_pid = window_pid[window_pid.rfind("= ") + 2 :]

            # print('found window', window.window_title)
            # print(' -> window_pid', window_pid)

            window_command = subprocess.run(
                ["ps", "-hp", window_pid, "-o", "command"],
                capture_output=True,
                text=True,
            )
            window_command_str = window_command.stdout.strip()

            # print(' -> window_command', window_command)

            executeOnStart.append(window_command_str)

        save_config(save_tree)

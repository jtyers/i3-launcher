import i3ipc
import inject
import os
import re
import subprocess
import time

from .config import SplitDirection
from .config import Config
from .config import Workspace
from .config import save_config


def strip_workspace_num(ws: i3ipc.WorkspaceReply) -> str | None:
    """Returns the name of the given workspace with any leading numbers stripped.
    Used to match an existing workspace to a profile name. None is returned if there
    is no name besides the numbers."""
    # strip any leading numbers from the workspace name; so
    # "3:www", "3 www", "3_www" and "3-www" all become "www"
    workspace_name = re.sub(r"^\d\s*[:\s_\-]\s*", "", ws.name)

    if workspace_name:
        return workspace_name
    return None


class I3Launcher:
    config = inject.attr(Config)
    connection = inject.attr(i3ipc.Connection)

    def next_workspace_num(self):
        """Returns the next available workspace number."""
        occupied = [ w.num for w in self.connection.get_workspaces() ]
        for i in range(1, 10):
            if i not in occupied:
                return i

        raise ValueError("no free workspace numbers (up to 9)")

    def find_workspace_for_profile(self, profile: Workspace) -> i3ipc.WorkspaceReply | None:
        """Finds any existing i3 workspaces with the same name as the given profile."""
        for ws in self.connection.get_workspaces():
            if strip_workspace_num(ws) == profile.name:
                return ws

        return None

    def get_current_workspace(self):
        return self.connection.get_tree().find_focused().workspace()

    def launch_all_workspaces(
        self,
    ):
        for w in self.config.workspaces:
            self.launch_workspace(w.name)

    def launch_workspace(self, workspace_name: str):
        """
        Launch the given workspace, if configured, and execute any on_start_exec commands.
        """
        profile = self.config.get_workspace(workspace_name)
        ws = self.find_workspace_for_profile(profile)
        num = self.next_workspace_num()

        if not ws or strip_workspace_num(self.get_current_workspace().name) != ws.name:
            self.connection.command(f'workspace "{num} {workspace_name}"')

        if profile.split == SplitDirection.VERTICAL:
            self.connection.command("layout splith")
        elif profile.split == SplitDirection.HORIZONTAL:
            self.connection.command("layout splitv")

        for cmd in profile.on_start_exec or []:
            _cmd = os.path.expanduser(os.path.expandvars(cmd))
            print("about to execute", _cmd)
            self.connection.command("exec " + _cmd)
            time.sleep(0.2)

    def save_workspace(self, all_workspaces: bool = False):
        """
        Save the currently running windows in the workspace with the given name
        to i3-launcher's config file. We do this by grabbing the matching workspace,
        finding each window and then finding the _NET_WM_PID, which tells us
        the PID that started that window, and then getting the full command
        for that PID.

        If all_workspaces is omitted, the currently focussed workspace is
        assumed.
        """

        workspaces: list[Workspace] = []

        tree = self.connection.get_tree()
        target_workspaces: list[i3ipc.Con] = []

        if all_workspaces:
            target_workspaces = list(tree.workspaces())

        else:
            # if no workspace provided, use the currently focussed one
            focused_window = self.connection.get_tree().find_focused()
            target_workspaces = [focused_window.workspace()]

        if not target_workspaces:
            raise ValueError("no workspaces found")

        for target_workspace in target_workspaces:
            # as usual, strip leading numbers from the workspace name
            workspace_name = re.sub(r"^\d\s*[:\s_\-]\s*", "", target_workspace.name)
            saved_workspace = self.config.get_workspace(workspace_name)

            if not saved_workspace:
                saved_workspace = Workspace(name=workspace_name)
                self.config.workspaces.append(saved_workspace)

            # note that we overwrite on_start_exec here, in all cases
            saved_workspace.on_start_exec = []

            for window in target_workspace.leaves():
                window_pid_xprop = subprocess.run(
                    ["xprop", "-id", hex(window.window), "_NET_WM_PID"],
                    capture_output=True,
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

                saved_workspace.on_start_exec.append(window_command_str)

            save_config(self.config)

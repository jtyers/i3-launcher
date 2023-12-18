import i3ipc
import inject
import re
import subprocess

from .config import Config
from .config import Workspace
from .config import save_config


class I3Launcher:
    config = inject.attr(Config)
    connection = inject.attr(i3ipc.Connection)

    def launch_all_workspaces(
        self,
    ):
        for w in self.config.workspaces:
            self.launch_workspace(w.name)

    def launch_workspace(self, workspace_name: str):
        """
        Launch the given workspace, if configured, and execute any on_start_exec commands.
        """
        # strip any leading numbers from the workspace name; so
        # "3:www", "3 www", "3_www" and "3-www" all become "www"
        workspace_name = re.sub(r"^\d\s*[:\s_\-]\s*", "", workspace_name)

        workspace = self.config.get_workspace(workspace_name)
        if not workspace:
            raise ValueError(f'no such workspace "{workspace_name}"')

        current_workspace = self.connection.get_tree().find_focused().workspace()
        if current_workspace.name != workspace_name:
            self.connection.command(f'workspace "{workspace_name}"')

        for cmd in workspace.on_start_exec or []:
            # run in connection context, since evt.old is actually gone
            print("about to execute", cmd)
            self.connection.command("exec " + cmd)

        i3_w = self.connection.get_tree().find_focused().workspace()
        self.connection.command(
            f'rename workspace to "{str(i3_w.num)}" "{workspace_name}"'
        )

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

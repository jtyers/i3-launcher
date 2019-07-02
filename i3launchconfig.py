# python module used to load/save the launch config
import os
import re
import json
import sys 
import subprocess
from threading import Thread, Event

save_file = os.path.expanduser('~/.config/i3/i3-launcher.json')

def load_config():
    """
    Loads the i3-launcher config from the config file, if it exists. The
    location is hard-coded to ~/.config/i3/i3-launcher.json.
    """
    save_tree = {}

    with open(save_file, 'r') as f:
        save_tree = json.load(f)

    return save_tree

def save_config(save_tree):
    """
    Saves the i3-launcher config from the config file, if it exists. The
    location is hard-coded to ~/.config/i3/i3-launcher.json.

    If the file is missing, an empty dict is returned.
    """
    with open(save_file, 'w') as f:
        json.dump(save_tree, f, indent=2)

def launch_workspace(connection, save_tree, workspace_name, launch_type = 'executeOnStart', rename = True):
    """
    Given a save_tree, launch and execute the start or finish 
    commands associated with a particular workspace name.
    """

    # strip any leading numbers from the workspace name; so
    # "3:www", "3 www", "3_www" and "3-www" all become "www"
    workspace_name = re.sub(r'^\d\s*[:\s_\-]\s*','', workspace_name)
    print('launch_workspace', workspace_name, launch_type)

    if save_tree.get(workspace_name):
        if save_tree[workspace_name].get(launch_type):
            for cmd in save_tree[workspace_name][launch_type]:
                # run in connection context, since evt.old is actually gone
                print('about to execute', cmd)
                connection.command('exec ' + cmd)

    if rename:
        workspace = connection.get_tree().find_focused().workspace()
        connection.command('rename workspace to "' + str(workspace.num) + ' ' + workspace_name + '"')

# https://stackoverflow.com/a/12435256/1432488
# https://stackoverflow.com/a/49007649/1432488
class Watcher(Thread):
    """
    Watcher that polls the save_tree_file and calls a function when it changes.
    """
    def __init__(self, call_func_on_change=None, *args, **kwargs):
        Thread.__init__(self)
        self.stopFlag = Event()

        self._cached_stamp = 0
        self.filename = save_file
        self.call_func_on_change = call_func_on_change
        self.args = args
        self.kwargs = kwargs

    # Look for changes
    def look(self):
        stamp = os.stat(self.filename).st_mtime
        if stamp != self._cached_stamp:
            self._cached_stamp = stamp
            # File has changed, so do something...
            if self.call_func_on_change is not None:
                self.call_func_on_change(*self.args, **self.kwargs)

    def run(self):
        while not self.stopFlag.wait(2.0):
            # call a function
            try: 
                self.look() 
            except KeyboardInterrupt: 
                self.stopFlag.set()
                break 

            except FileNotFoundError:
                # Action on file not found
                pass
            except: 
                print('Unhandled error: %s' % sys.exc_info()[0])

    def stop(self):
        self.stopFlag.set()

def save_workspace_state_to_config(connection, workspace_name = None):
    """
    Save the currently running windows in the workspace with the given name 
    to i3-launcher's config file. We do this by grabbing the matching workspace,
    finding each window and then finding the _NET_WM_PID, which tells us
    the PID that started that window, and then getting the full command
    for that PID.

    If workspace_name is omitted, the currently focussed workspace is 
    assumed.
    """
    save_tree = {}

    try:
        save_tree = load_config()

    except FileNotFoundError:
        pass # ignore and use empty dict

    tree = connection.get_tree()
    target_workspace = None
  
    if not workspace_name:
        # if no workspace provided, use the currently focussed one
        focused_window = connection.get_tree().find_focused()
        target_workspace = focused_window.workspace()
        workspace_name = target_workspace.name

    else:
        # otherwise, find the workspace corresponding to that name

        # find the workspace and workspace_save_tree
        for workspace in tree.workspaces():
            if workspace.name == workspace_name:
                target_workspace = workspace

    if not target_workspace:
        raise ValueError('no workspace found with the name "' + workspace_name + '"')

    # as usual, strip leading numbers from the workspace name
    workspace_name = re.sub(r'^\d\s*[:\s_\-]\s*','', workspace_name)
    workspace_save_tree = save_tree.get(workspace_name)

    if not workspace_save_tree:
        workspace_save_tree = {}
        save_tree[workspace_name] = workspace_save_tree

    # note that we overwrite executeOnStart here, in all cases
    executeOnStart = []
    workspace_save_tree['executeOnStart'] = executeOnStart

    for window in target_workspace.leaves():        

        window_pid_xprop = subprocess.run(['xprop', '-id', hex(window.window), '_NET_WM_PID'], capture_output=True)
        window_pid = window_pid_xprop.stdout.strip().decode()
        window_pid = window_pid[window_pid.rfind('= ')+2:]
        
        #print('found window', window.window_title)
        #print(' -> window_pid', window_pid)

        window_command = subprocess.run(['ps', '-hp', window_pid, '-o', 'command'], capture_output=True)
        window_command = window_command.stdout.strip().decode()
        
        #print(' -> window_command', window_command)

        executeOnStart.append(window_command)

    save_config(save_tree)

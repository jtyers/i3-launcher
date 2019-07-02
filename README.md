# i3-launcher

Save the applications running in your i3 workspace, then load the workspace again later and auto-spawn those same applications.

## Why?

Some of us like to use our window manager workspaces "per-project", where each workspace is a project or topic that we're working on (for example, one might be "general browsing", another might be "personal website", another might be "my ecommerce shop" and so on). This works really well when you're able to run per-project web browsing sessions (separating your time-wasting browsing from your work browsing) or per-project IDE sessions, separating your coding on a hobby project from your work projects. See below for my recommended list of apps to use this with which enable this.

## How

You'll need:
 * `python3`
 * `i3ipc` (usually `python-i3ipc` in your distro package manager, or `i3ipc` in `pip`)
 * `xprop` (usually `xprop` or `xorg-xprop` in your distro package manager)
 * `rofi`
 * `dynmen` (`pip install dynmen`)

1. Install the dependencies above
2. Clone this repo
3. Run `i3-launcher`

A menu will pop up, allowing you to load or save your workspace. Configuration is stored in `~/.config/i3/i3-launcher.json`. When you save a workspace, `i3-launcher` will go through all your windows, look for the PID of the owning process of each window, and add the command line that started that PID to your configuration. Some of the apps I use require tweaking of the command lines, for example when they are launched via wrapper scripts that use `exec`.

## Recommended

`i3-launcher` makes me way more productive. However, using applications that support multiple sessions/profiles, so that they can be opened on a per-project basis make this even more powerful. Here is what I use:

* [`kitty`](https://sw.kovidgoyal.net/kitty/) terminal (most terminals support profiles though)
* [`qutebrowser`](https://qutebrowser.org/) for keyboard-driven browser, with vi-like key bindings (uses WebEngine under the hood, same engine as Chrome/Chromium, and supports developer tools and most sites with no problems)
* [`qutebrowser wrapper script` by ayekat](https://github.com/ayekat/dotfiles/blob/a236c0fa1cf5e4c4c3e9325295ba5fe8c0d9eb44/lib/dotfiles/bin/qutebrowser) which adds multiple-profile support to qutebrowser
* [`SpaceVim`](https://spacevim.org/) as a lightweight, Vim-driven IDE

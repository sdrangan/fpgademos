---
title: SSH connection
parent: NYU Remote Server
nav_order: 1
has_children: False
---
## Connecting via SSH

This simplest way to connect to the NYU remote server is via SSH.
You need to be on the NYU network or connected via VPN. Then use the following settings:

- **Host**: any of `ecs03.poly.edu` through `ecs06.poly.edu`
    - Note:  Previous versions of the class used `ecs02.poly.edu`.  This server has not been upgraded with the latest Vitis / Vivado tools.  Do not use this.
- **Username**: your NetID
- **Port**: 22

You can connect using any SSH client. Below are the recommended options depending on your operating system.

---

## Windows: MobaXterm

[MobaXterm](https://mobaxterm.mobatek.net/) is an excellent GUI SSH client for Windows.

1. Create a new **SSH session** using the settings above.
2. Log in with your NetID and password.
3. You will get:
   - A terminal connected to the remote machine
   - A **remote file explorer** panel on the left

You can drag and drop files between your local machine and the remote server. This is the easiest and most reliable method for Windows users, especially because Windows PowerShell’s `scp` does **not** work with the NYU EDA servers due to server‑side banner output.

---

## macOS Terminal or Windows PowerShell

You can always log in from a terminal using:

```bash
ssh <netid>@ecs03.poly.edu
```

You may choose any of `ecs03` through `ecs06`.

### macOS users

macOS includes a robust OpenSSH implementation, so you can also use `scp` to copy files:

```bash
scp <netid>@ecs03.poly.edu:/home/<netid>/submission.py .
```

This downloads `submission.py` into your current local directory.

### Windows users

The command `scp` **will not work** in Windows PowerShell because the NYU servers print a banner message that breaks PowerShell’s `scp`. Windows users should use **MobaXterm** or **VS Code Remote‑SSH** instead.

---

## VS Code Remote‑SSH (macOS, Windows, Linux)

If you use VS Code, the **Remote – SSH** extension provides a full development environment on the remote machine.

### Setup

1. Install the **Remote – SSH** extension in VS Code.
2. Open the **Remote Explorer** panel (icon on the left sidebar).
3. Under **SSH Targets**, click the **+** to add a new host.
4. Enter:
   ```
   ssh <netid>@ecs03.poly.edu
   ```
5. Choose your user SSH config file when prompted
   - Windows: `C:\Users\<username>\.ssh\config`
   - macOS/Linux: `~/.ssh/config`
6. Connect to the host. Wait for the status bar at the bottom left to turn green
   and read `SSH: ecs03.poly.edu` — until it does, you are still browsing your
   own machine.
7. **File → Open Folder**, and choose the **repository** directory, normally
   `/home/<netid>/hwdesign`.

{: .note }
> **Open the repository folder, not your home directory.** VS Code keys a great
> deal off the folder you open. The Python extension looks for `.venv` relative
> to it, so opening your home directory means the environment you built in
> [Using Python](./python.md) is never found, and every `import waveflow` is
> marked as an error even though the code runs fine. Opening your home directory
> also makes VS Code watch and search everything beneath it — including the
> several-hundred-megabyte `~/.vscode-server` tree and the EDA tool directories
> — which makes the window noticeably sluggish, since home directories on these
> servers are network-mounted.

### Course developers

If you are following the [developer setup](../repo/developer.md), you may want
both the `waveflow` and `hwdesign` folders open at once. You do **not** need two
VS Code windows, and you should not open your home directory to get both.
Instead, use a **multi-root workspace**:

1. Open `~/hwdesign` as above.
2. **File → Add Folder to Workspace…** and choose `~/waveflow`.
3. **File → Save Workspace As…** and save it — for example as
   `~/hwdesign.code-workspace`.

Both repositories now appear as top-level folders in a single Explorer, with
search, `Ctrl+P`, and Source Control spanning the pair. Each folder keeps its own
settings, and the editable install means an edit in `waveflow` takes effect in
`hwdesign` immediately. Reopen the pair later from **File → Open Workspace from
File…**, or from the **Recent** list.

This is only useful with the editable install described on that page. Students
install `waveflow` as a package and never clone it, so a single `~/hwdesign`
folder is all they need.

### What you get

- A full VS Code environment running **on the remote machine**
- A remote terminal
- A remote file explorer
- The ability to **download or upload files** via right‑click or drag‑and‑drop
- The ability to edit files directly on the remote server with IntelliSense, syntax highlighting, etc.

This is the best option for macOS users and an excellent alternative for Windows users who prefer VS Code over MobaXterm.

---

## If SSH warns that the host key has changed

When connecting you may be stopped by a warning like this, and the connection
refused:

```
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
@    WARNING: REMOTE HOST IDENTIFICATION HAS CHANGED!      @
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@
...
Offending ECDSA key in C:\Users\<username>/.ssh/known_hosts:6
Host key verification failed.
```

Your SSH client remembers an identifying key for every server you have
connected to, and refuses to continue when the key it is offered does not match
the one it recorded. The EDA servers were reinstalled during the recent tools
upgrade, and a reinstalled machine generates new keys — so if you connected to
these servers in a previous semester, you will see this.

Remove the stored key and reconnect:

```bash
ssh-keygen -R ecs03.poly.edu
```

Substitute whichever host you are connecting to. The command rewrites
`known_hosts` and leaves a backup in `known_hosts.old`; it works on Windows,
macOS, and Linux. Reconnect and answer `yes` when asked to accept the new key.

Prefer this to editing `known_hosts` by hand — a single host can occupy several
lines, and deleting the wrong one is easy.

{: .note }
> If VS Code Remote-SSH fails to connect with only a generic "could not
> establish connection" message, try connecting from a terminal first. VS Code
> hits the same host key check but reports it far less clearly.

{: .warning }
> This warning also has a genuine security meaning, and a routine server rebuild
> looks exactly like an attempted interception. Clearing the key is the right
> move here because we know these servers were reinstalled. On a machine you have
> no such explanation for, do not clear the key — contact whoever administers it.

---

Go to [GUI connection with Fast-X](./fastx.md)

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
6. Connect to the host and select a folder (typically your home directory).

### What you get

- A full VS Code environment running **on the remote machine**
- A remote terminal
- A remote file explorer
- The ability to **download or upload files** via right‑click or drag‑and‑drop
- The ability to edit files directly on the remote server with IntelliSense, syntax highlighting, etc.

This is the best option for macOS users and an excellent alternative for Windows users who prefer VS Code over MobaXterm.

---

Go to [GUI connection with Fast-X](./fastx.md)

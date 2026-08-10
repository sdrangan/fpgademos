---
title: Setting up Git and GitHub
parent: NYU Remote Server
nav_order: 4
has_children: False
---
# Setting up Git and GitHub on the NYU Server

You need Git working on the server for two reasons:

1. To **clone the course repository**, `hwdesign`, so you have the labs and demos.
2. To **push your own work** — your project repository, and anything you fork.

You do **not** need to clone `waveflow`. It installs directly from GitHub as a package;
see [Installing the Python packages](../repo/package.md). Clone it only if you intend to
modify the framework itself.

Git is already installed on the servers (version 2.52 at the time of writing), so there
is nothing to install for step 1. Authentication is the part that needs setting up.

---

## 1. Tell Git who you are

Git stamps every commit with a name and email. Set them once:

```bash
git config --global user.name "Your Name"
git config --global user.email "your_netid@nyu.edu"
```

Use the same email as your GitHub account, or GitHub will not connect your commits to
your profile.

## 2. Clone the course repository

Cloning a public repository needs no authentication at all, so you can do this
immediately:

```bash
cd ~
git clone https://github.com/sdrangan/hwdesign.git
```

Then follow [Using Python](./python.md) to build the environment and install the
packages.

{: .note }
> This is enough to *do the labs*. The rest of this page is about pushing your own work
> back to GitHub, which you will need for your project.

---

## 3. Authenticate so you can push

Pushing requires proving who you are. Cloning over HTTPS as above leaves Git prompting
for a username and password on every push, and GitHub stopped accepting account
passwords years ago — so this step is not optional once you start writing.

**Use the GitHub CLI (`gh`).** It handles authentication for both `gh` *and* `git`, so
you set up credentials once rather than twice, and it needs no manually created access
token.

### Install `gh`

`gh` is not installed on the EDA servers, and you cannot install system software. Install
it into your home directory instead — the same approach used for `uv` in
[Using Python](./python.md):

```bash
mkdir -p ~/.local/bin
cd /tmp
curl -fsSL https://github.com/cli/cli/releases/download/v2.97.0/gh_2.97.0_linux_amd64.tar.gz -o gh.tgz
tar xzf gh.tgz
cp gh_2.97.0_linux_amd64/bin/gh ~/.local/bin/
chmod +x ~/.local/bin/gh
```

{: .note }
> Version 2.97.0 is pinned above because the download filename contains the version
> number. Any recent release works — check
> [the releases page](https://github.com/cli/cli/releases/latest) for a newer one and
> substitute the number in all three places.

If you already followed [Using Python](./python.md), `~/.local/bin` is on your path
already. Check:

```bash
gh --version
```

If that reports `Command not found`, add the directory to your path as described in
[Using Python](./python.md#if-your-shell-is-tcsh).

### Log in

```bash
gh auth login
```

Answer the prompts: **GitHub.com** → **HTTPS** → **Yes** (authenticate Git with your
GitHub credentials) → **Login with a web browser**.

`gh` then prints an eight-character code and a URL. Open that URL on your **laptop**
(not on the server — there is no browser there), paste the code, and approve. The
terminal completes on its own.

This is the reason to prefer the browser flow: it works fine over SSH, and you never
create or copy a token by hand.

### Point Git at the same credentials

```bash
gh auth setup-git
```

This configures Git to ask `gh` for credentials, so `git push` and `git pull` just work
from then on — no prompts, no token pasting.

### Check it

```bash
gh auth status
```

You should see `Logged in to github.com account <your-username>`.

---

## 4. Working with your own repositories

With the above done, everything behaves normally:

```bash
gh repo create my-project --private --clone     # create and clone in one step
cd my-project
# ... work ...
git add -A
git commit -m "First version"
git push
```

To work on an existing repository of yours:

```bash
gh repo clone <your-username>/<your-repo>
```

`gh` is also how you open pull requests and read issues without leaving the terminal:

```bash
gh pr create --fill
gh pr status
gh issue list
```

---

## 5. If you use Claude or another AI coding agent

Agents cannot open a browser, so they rely on credentials already stored on disk. The
setup above is exactly what they need: `gh auth login` writes `~/.config/gh/hosts.yml`,
and `gh auth setup-git` makes Git use it. An agent running in your account can then
clone, commit, push, and open pull requests on your behalf with no further configuration.

Two things are worth knowing:

**`~/.local/bin` may not be on the agent's path.** Agents often start a shell that does
not read your shell startup files the same way your terminal does. If an agent reports
that `gh` is not found, tell it to use the full path `~/.local/bin/gh`.

**An exported token overrides the stored login.** If you set `GH_TOKEN` in your
environment, `gh` uses it and *refuses to store credentials* — you will see:

```
The value of the GH_TOKEN environment variable is being used for authentication.
To have GitHub CLI store credentials instead, first clear the value from the environment.
```

Nothing is saved, so an agent (whose shell does not have your variable) stays
unauthenticated. If you have already created a token and want to keep using it, store it
explicitly with the variable stripped from `gh`'s own environment:

```bash
echo $GH_TOKEN | env -u GH_TOKEN gh auth login --with-token
```

Otherwise just use `gh auth login` as above and do not set `GH_TOKEN` at all — one
credential in one place is simpler to reason about and to revoke.

---

## Security on a shared machine

These servers are shared, and authentication leaves a long-lived credential in your home
directory (`~/.config/gh/hosts.yml`, and `~/.git-credentials` if you use a token).

- **Check your home directory is private.** It should be, by default:

  ```bash
  ls -ld ~
  ```

  The permissions should begin `drwx------`. If they do not, fix it with
  `chmod 700 ~`.

- **Never commit secrets.** API keys, tokens, and passwords do not belong in a
  repository — including a private one. Once pushed, a secret is in the history even
  after you delete the file.

- **Log out when you are done with the machine** if you would rather not leave a
  credential behind:

  ```bash
  gh auth logout
  ```

- **Revoke rather than repair** if you ever think a credential leaked: delete it at
  <https://github.com/settings/tokens> (or under *Settings → Applications* for the CLI's
  authorization) and log in again.

---

Go to [using Python](./python.md)

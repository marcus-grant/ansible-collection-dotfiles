# Ansible Collection - marcus_grant.dotfiles

My ansible collection for managing dotfiles and shell configurations.
There's some previous work here that I'm not re-using till
I've had time to review and modify it to my current standards.
Any of the roles that exist in this collection but
not listed below are of low quality and should not be used.

## Development

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Unit tests (collection modules)

```bash
source venv/bin/activate
python -m pytest tests/unit/ -v
```

### Module integration tests

Collection modules are tested via a collection-level molecule scenario.
Run from the **collection root**:

```bash
source venv/bin/activate
# Install the current working copy so Ansible picks up local changes
ansible-galaxy collection install . --force
molecule test -s dotfiles_git
```

> **Important:** `ansible-galaxy collection install . --force` must be run before
> every molecule test cycle when working on collection modules. Molecule uses the
> installed copy at `~/.ansible/collections/`, not the local working tree.

### Role molecule tests

Run from the **role directory**:

```bash
source ../../venv/bin/activate   # activate from the role directory
# If the role uses any collection module (e.g. dotfiles_git), reinstall first:
ansible-galaxy collection install ../.. --force
molecule test
```

Step-by-step during development:

```bash
molecule create
molecule converge
molecule verify
molecule destroy
```

## Modules

### `marcus_grant.dotfiles.dotfiles_git`

Clones a dotfiles git repository and places config files at the locations
programs expect them. Supports two placement methods:

- **shim** *(default)*: writes a shell file containing a `source` line pointing
  into the cloned repo. Idempotent — only written when content differs.
  Use for shell-sourced files (zsh, bash, profile).
- **symlink**: creates a symlink at the target path. Use for non-shell config
  files that cannot interpret a `source` line (vim, tmux, git).

**Requirements:** The `git` binary must be present on the target host before invoking this module.

**SSH pre-flight check:** When `repo` is an SSH URL (`git@…` or `ssh://…`), the
module asserts that SSH is properly configured before attempting the clone:

1. `~/.ssh/known_hosts` must exist and contain the repo hostname.
2. Either `~/.ssh/config.d/managed-<hostname>.conf` must exist, or `~/.ssh/config`
   must reference the hostname.

If either check fails the module aborts immediately with a clear error message
rather than hanging on an interactive SSH prompt. This enforces the soft
dependency on the `ssh_config` role: run `ssh_config` before any role that uses
`dotfiles_git` with an SSH URL.

Full parameter reference: `ansible-doc marcus_grant.dotfiles.dotfiles_git`

**Minimal example:**

```yaml
- name: Clone zsh dotfiles and place shims
  marcus_grant.dotfiles.dotfiles_git:
    repo: https://github.com/yourname/dots-zsh
    dest: ~/.config/zsh
    files:
      - src: rc.zsh
        dest: ~/.zshrc
      - src: env.zsh
        dest: ~/.zshenv
        prepend_lines:
          - source $HOME/.profile
      - src: profile.zsh
        dest: ~/.zprofile
```

**Parameters:**

| Parameter | Required | Default | Description |
|-----------|----------|---------|-------------|
| `repo` | yes | — | Git repository URL. Supports HTTPS and SSH (SSH triggers pre-flight check; requires `ssh_config` role to have run). |
| `dest` | yes | — | Clone destination (tilde expanded) |
| `version` | no | `HEAD` | Git ref to check out |
| `force` | no | `false` | Delete and re-clone even if repo exists |
| `update` | no | `false` | Run `git pull` on existing clone; reports `changed` if commits were fetched |
| `files` | no | `[]` | List of file placement mappings (see below) |

Each entry in `files`:

| Key | Required | Default | Description |
|-----|----------|---------|-------------|
| `src` | yes | — | File path relative to `dest` (inside the clone) |
| `dest` | yes | — | Absolute path where the program expects this file |
| `method` | no | `shim` | `shim` or `symlink` |
| `mode` | no | `0600` | File permissions (shim only) |
| `prepend_lines` | no | `[]` | Lines written before the `source` line (shim only) |

---

## Roles

* **profile**
  * *Description*:
    Sets up the user's shell profile via templating the `~/.profile` file.
  * [*Role link!*](./roles/profile/)
  * **TODO**:
    * Add support for a profile.d folder and sourcing it lexically
      * Allows for other roles to add their own profile configurations.
* **ssh**
  * *Description*:
    Sets up SSH environtment (config, add keys, instruct manual entry).
  * [*Role link!*](./roles/ssh/)
* **ssh_transfer_key**
  * *Description*:
    Deploys existing SSH key pairs from the Ansible control node to a target host.
    Creates `~/.ssh/` with correct permissions and deploys private and public key
    files with correct ownership. No key generation, no `authorized_keys`, no config.
  * [*Role link!*](./roles/ssh_transfer_key/)
* **ssh_keygen**
  * *Description*:
    Generates SSH keypairs on the target host. Idempotent — skips generation if
    the private key already exists unless forced. Supports ed25519 (default), rsa,
    and ecdsa. No distribution, no `authorized_keys`, no config.
  * [*Role link!*](./roles/ssh_keygen/)
* **ssh_authorize**
  * *Description*:
    Distributes SSH public keys to `authorized_keys` on destination hosts via
    controller delegation. Topology from `ssh_config_entries` (opt-in via
    `ssh_authorize: true`) plus an `ssh_authorize_extra` list. No direct
    source-to-destination connectivity required.
  * [*Role link!*](./roles/ssh_authorize/)
* **git**
  * *Description*:
    Installs git & optional extras and configures global git configs.
  * [*Role link!*](./roles/git/)
* **neovim**
  * *Description*:
    Installs neovim via package manager &
    clones a repository containing its configurations.
  * [*Role link!*](./roles/neovim/)
* **userdirs**
  * *Description*:
    Sets up shell `userdirs` using custom list and `XDG_`* variables.
  * [*Role link!*](./roles/userdirs/)
* **bash**
  * A role that installs, sets as default shell, git clones a dotfiles repo,
    and symlinks all expected file locations to
    their respective locations in the dotfile repo.
  * [*Role link!*](./roles/bash/)
* **zsh**
  * A role that installs then configures a ZSH shell environment using
    a clone git repo of ZSH dotfiles.
  * [*Role link!*](./roles/zsh/)
* **gpg_transfer**
  * *Description*:
    Transfers existing GPG key material from an Ansible controller to target hosts.
    Supports full key export or subkeys-only export per key. Copies ownertrust and
    `gpg.conf`, writes `gpg-agent.conf`, and optionally creates a `~/.gnupg` symlink
    pointing to a custom gnupg home. Idempotent — only transfers keys not already
    present on the target. Passphrase must be supplied interactively via `vars_prompt`.
  * [*Role link!*](./roles/gpg_transfer/)
* **nodejs_system**
  * *Description*:
    System-level Node.js installation and management. Installs Node.js/npm 
    via package manager and optionally installs global npm packages and 
    additional distribution packages.
  * [*Role link!*](./roles/nodejs_system/)
  * **Features**:
    * Cross-platform support (Debian/Ubuntu, RedHat/Fedora)
    * Global npm package installation
    * Distribution-specific Node.js package installation
    * Comprehensive molecule testing

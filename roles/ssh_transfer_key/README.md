# marcus_grant.dotfiles.ssh_transfer_key

Deploys SSH key pairs from the Ansible control node to a target host.
Creates `~/.ssh/` with correct permissions and copies private and public
key files with correct ownership. Nothing else — no key generation, no
`authorized_keys`, no `~/.ssh/config`.

## Requirements

No system dependencies beyond a POSIX `getent` (present on all supported
Linux targets).

## Role Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ssh_transfer_key_owner` | no | `ansible_user_id` | User who owns `~/.ssh/` and all deployed key files |
| `ssh_transfer_key_pairs` | yes | `[]` | List of key pairs to deploy (see below) |

### `ssh_transfer_key_pairs` entries

Each entry in `ssh_transfer_key_pairs` supports:

| Key | Required | Description |
|---|---|---|
| `src` | yes | Path to the private key on the **control node**. Supports `~`-expansion. |
| `name` | no | Filename for the key on the target. Defaults to `basename(src)`. |

The role infers the public key path by appending `.pub` to `src`. If the
`.pub` file does not exist on the control node, it is silently skipped.

## Behavior

- `~/.ssh/` is created with mode `0700` if absent
- Private keys are deployed with mode `0600`
- Public keys are deployed with mode `0644` (when the `.pub` exists)
- All files are owned by `ssh_transfer_key_owner`
- Idempotent — re-running with unchanged source files produces no changes
- Content changes at the source propagate on the next run (standard `copy` behavior)
- `no_log: true` is applied to all tasks that handle private key content

## Dependencies

None.

## Example Playbook

```yaml
- hosts: workstations
  become: true
  roles:
    - role: marcus_grant.dotfiles.ssh_transfer_key
      vars:
        ssh_transfer_key_owner: marcus
        ssh_transfer_key_pairs:
          - src: ~/.ssh/id_ed25519_git
            name: id_ed25519_git
          - src: ~/.ssh/id_ed25519_personal
            name: id_ed25519_personal
```

After this role runs, the target will have:

```
~/.ssh/                       0700  marcus:marcus
~/.ssh/id_ed25519_git         0600  marcus:marcus
~/.ssh/id_ed25519_git.pub     0644  marcus:marcus
~/.ssh/id_ed25519_personal    0600  marcus:marcus
```

## Playbook Integration

### Version

Introduced in `marcus_grant.dotfiles` **1.3.0**.

### Installation

```bash
ansible-galaxy collection install marcus_grant.dotfiles:>=1.3.0
```

### Ordering

`ssh_transfer_key` must run **before** any role that clones a git repository over
an SSH URL. It has no Ansible role dependencies — schedule it by task
ordering in the play, not via `dependencies`.

Recommended sequence:

```
ssh_transfer_key → (roles that clone via SSH) → ssh_config → ssh_authorize
```

### Minimal example

```yaml
- hosts: workstations
  become: true
  roles:
    - role: marcus_grant.dotfiles.ssh_transfer_key
      vars:
        ssh_transfer_key_owner: marcus
        ssh_transfer_key_pairs:
          - src: ~/.ssh/id_ed25519_git
```

### Full example

```yaml
- hosts: workstations
  become: true
  roles:
    - role: marcus_grant.dotfiles.ssh_transfer_key
      vars:
        ssh_transfer_key_owner: marcus
        ssh_transfer_key_pairs:
          - src: ~/.ssh/id_ed25519_git
            name: id_ed25519_git
          - src: ~/.ssh/id_ed25519_personal
            name: id_ed25519_personal
    - role: marcus_grant.dotfiles.zsh
      vars:
        zsh_git_repo: git@github.com:marcus/dots-zsh.git
```

### Key paths on the control node

`src` is evaluated on the **control node** (the machine running
`ansible-playbook`), not on the target. Both absolute paths and
`~`-expanded paths are supported. The `.pub` file is optional — if it
does not exist at `src + ".pub"` the role skips it without error.

### Security notes

- Private key content is never logged (`no_log: true` throughout)
- `~/.ssh/` is created `0700`; private keys land `0600`; public keys `0644`
- All files are owned by `ssh_transfer_key_owner`, not `root`
- The role does **not** generate keys, modify `authorized_keys`, or touch
  `~/.ssh/config` — those are separate concerns

## License

GPL-2.0-or-later

## Author Information

Marcus Grant
[marcusfg@protonmail.com](mailto:marcusfg@protonmail.com)
[github.com/marcus-grant](https://github.com/marcus-grant)

# marcus_grant.dotfiles.ssh_keys

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
| `ssh_keys_owner` | no | `ansible_user_id` | User who owns `~/.ssh/` and all deployed key files |
| `ssh_keys_pairs` | yes | `[]` | List of key pairs to deploy (see below) |

### `ssh_keys_pairs` entries

Each entry in `ssh_keys_pairs` supports:

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
- All files are owned by `ssh_keys_owner`
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
    - role: marcus_grant.dotfiles.ssh_keys
      vars:
        ssh_keys_owner: marcus
        ssh_keys_pairs:
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

## License

GPL-2.0-or-later

## Author Information

Marcus Grant
[marcusfg@protonmail.com](mailto:marcusfg@protonmail.com)
[github.com/marcus-grant](https://github.com/marcus-grant)

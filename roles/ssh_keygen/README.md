# marcus_grant.dotfiles.ssh_keygen

Generates SSH keypairs on the target host. Idempotent — skips generation if
the private key already exists unless `ssh_keygen_force` is set. Creates
`~/.ssh/` with correct permissions if absent.

Does **not** distribute public keys, manage `authorized_keys`, or touch
`~/.ssh/config` — those are separate concerns handled by `ssh_authorize` and
`ssh_config`.

## Requirements

`openssh` (specifically the `ssh-keygen` binary) must be present on the target
host before this role runs. It is not installed by this role.

## Role Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ssh_keygen_owner` | **yes** | — | User who owns `~/.ssh/` and all generated key files. Resolved via `getent passwd`. |
| `ssh_keygen_keys` | no | `[]` | List of keypairs to generate (see below) |
| `ssh_keygen_force` | no | `false` | When `true`, regenerates keys even if they already exist. **Never set in vars files** — pass as `-e ssh_keygen_force=true`. |

### `ssh_keygen_keys` entries

Each entry in `ssh_keygen_keys` supports:

| Key | Required | Default | Description |
|---|---|---|---|
| `name` | no | `id_{{ type }}` | Filename in `~/.ssh/` |
| `type` | no | `ed25519` | Key type: `ed25519`, `rsa`, `ecdsa` |
| `bits` | no | omitted | Key size. Only meaningful for `rsa`/`ecdsa`; ignored for `ed25519`. |
| `comment` | no | `{{ ssh_keygen_owner }}@{{ inventory_hostname }}` | Key comment (`-C` flag) |
| `passphrase` | no | `""` | Key passphrase (`-N` flag). Empty string = no passphrase. Use ansible-vault in practice. |

## Behavior

- `~/.ssh/` is created with mode `0700` if absent
- Private keys land at mode `0600`, owned by `ssh_keygen_owner`
- Public keys land at mode `0644`, owned by `ssh_keygen_owner`
- If the private key already exists and `ssh_keygen_force` is `false`, generation is skipped — existing keys are never overwritten automatically
- `no_log: true` is applied to the generation task (passphrase appears in the command)

## Dependencies

None. Soft companion roles:
- `ssh_config` — configure SSH client after keys exist
- `ssh_authorize` — distribute public keys to `authorized_keys` on remote hosts

## Example Playbook

```yaml
- hosts: workstations
  become: true
  roles:
    - role: marcus_grant.dotfiles.ssh_keygen
      vars:
        ssh_keygen_owner: marcus
        ssh_keygen_keys:
          - name: id_ed25519_git
          - name: id_rsa_legacy
            type: rsa
            bits: 4096
            comment: marcus@legacy-server
```

After this role runs, the target will have:

```
~/.ssh/                    0700  marcus:marcus
~/.ssh/id_ed25519_git      0600  marcus:marcus
~/.ssh/id_ed25519_git.pub  0644  marcus:marcus
~/.ssh/id_rsa_legacy       0600  marcus:marcus
~/.ssh/id_rsa_legacy.pub   0644  marcus:marcus
```

## Playbook Integration

### Version

Introduced in `marcus_grant.dotfiles` **1.12.0**.

### Installation

```bash
ansible-galaxy collection install marcus_grant.dotfiles:>=1.12.0
```

### Ordering

`ssh_keygen` should run before any role that requires the key files to exist
on the target (e.g. `ssh_config` referencing `IdentityFile`, or `ssh_authorize`
distributing the public key).

Recommended sequence:

```
ssh_keygen → ssh_config → (roles that clone via SSH) → ssh_authorize
```

### Force regeneration (manual test)

To force-regenerate all keys in a molecule scenario:

```bash
molecule converge -- -e ssh_keygen_force=true
```

This is intentionally not automated — force regeneration destroys existing keys
and should require explicit operator intent.

### Security notes

- Passphrase is never logged (`no_log: true` on generation task)
- `~/.ssh/` is created `0700`; private keys land `0600`; public keys `0644`
- All files are owned by `ssh_keygen_owner`, not `root`
- The role does **not** overwrite existing keys unless `ssh_keygen_force=true`

## License

GPL-2.0-or-later

## Author Information

Marcus Grant
[marcusfg@protonmail.com](mailto:marcusfg@protonmail.com)
[github.com/marcus-grant](https://github.com/marcus-grant)

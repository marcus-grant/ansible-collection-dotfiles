# marcus_grant.dotfiles.ssh_authorize

Distributes SSH public keys to `authorized_keys` on destination hosts, brokered
entirely by the Ansible controller. The source host's pubkeys are slurped by the
controller and written to each destination via `delegate_to` — no direct
source→destination SSH connectivity is required.

Optionally also writes the source host's pubkey into the **controller's** own
`authorized_keys`, enabling the source to SSH back into the controller.

## Requirements

- `openssh-client` (or equivalent) must be present on the **source** host so that
  pubkey files exist to read.
- Destination hosts must be reachable by the Ansible controller.
- The source user must already have keypairs in `~/.ssh/` before this role runs.
  Use `ssh_keygen` to generate them if needed.

## Role Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `ssh_authorize_owner` | **yes** | — | User on both source and destination. Pubkeys are read from this user's `~/.ssh/` on the source; written to their `authorized_keys` on each destination. Resolved via `getent passwd`. |
| `ssh_config_entries` | no | `[]` | List of destination entries, filtered to those with `ssh_authorize: true`. Mirrors the shape of `ssh_config` host entries (see below). |
| `ssh_authorize_extra` | no | `[]` | Additional destination entries not covered by `ssh_config_entries`. Same format, no filtering — all entries are processed. |
| `ssh_authorize_force` | no | `false` | When `true`, uses regexp-based matching on key-type + comment to replace a stale key line in `authorized_keys`. When `false`, exact-line match is used (no-op if already present). **Never set in vars files — pass as `-e ssh_authorize_force=true`.** |
| `ssh_authorize_controller_user` | no | — | When defined, authorizes the source host's pubkey(s) into this user's `authorized_keys` on the Ansible controller. Acts as the feature enabler — if unset, the entire controller block is skipped. Resolved via `getent passwd` delegated to `localhost`. |
| `ssh_authorize_controller_identity_file` | no | — | When set alongside `ssh_authorize_controller_user`, only this key (filename stem, no `.pub`) is pushed to the controller instead of all already-slurped pubkeys. The key is slurped directly from the source host — it need not appear in any destination entry. Requires `ssh_authorize_controller_user`. |

### Destination entry format

Both `ssh_config_entries` and `ssh_authorize_extra` accept entries with:

| Key | Required | Default | Description |
|---|---|---|---|
| `name` | **yes** | — | Ansible inventory hostname of the destination. Used as `delegate_to` target. |
| `identity_file` | no | `id_ed25519` | Filename (no extension) of the keypair in `~/.ssh/`. The `.pub` file is read. |
| `ssh_authorize` | no | — | Set to `true` to include this entry when sourced from `ssh_config_entries`. Entries without this key, or with `false`, are filtered out. |

## Topology resolution

1. `ssh_config_entries` is filtered to entries where `ssh_authorize: true` is
   explicitly set. Absent or `false` → excluded.
2. The filtered list is concatenated with `ssh_authorize_extra`.
3. The combined list is processed identically — one loop, same delegated tasks.

## Pubkey resolution

- Entry has `identity_file: foo` → `~/.ssh/foo.pub` on the source host.
- Entry has no `identity_file` → `~/.ssh/id_ed25519.pub` on the source host.
- Identical `identity_file` values across multiple entries are deduplicated —
  the file is slurped once regardless of how many destinations reference it.

## Behavior

- `~/.ssh/` is created on the destination with mode `0700` if absent.
- `authorized_keys` is created on the destination with mode `0600` if absent.
- Ownership of both is set to `ssh_authorize_owner`.
- `force: false` (default): `lineinfile` exact-line match — no-op if the pubkey
  line is already present.
- `force: true`: regexp match on `^<key-type> .* <comment>$` — replaces a stale
  line (e.g. after key regeneration) if comment matches; adds fresh if no match.
  Falls back to exact-line match for keys with no comment field.

## Dependencies

None (pure `ansible.builtin.*`). Soft companion roles:

- `ssh_keygen` — generate keypairs on the source host before running this role
- `ssh_config` — `ssh_config_entries` from that role feeds directly into
  `ssh_authorize`'s topology when entries carry `ssh_authorize: true`

Recommended ordering:

```
ssh_keygen → ssh_config → ssh_authorize
```

## Example Playbook

```yaml
- hosts: workstations
  become: true
  roles:
    - role: marcus_grant.dotfiles.ssh_authorize
      vars:
        ssh_authorize_owner: marcus
        ssh_config_entries:
          - name: server1
            identity_file: id_ed25519_server
            ssh_authorize: true
          - name: server2
            ssh_authorize: true
          - name: work-laptop
            # no ssh_authorize: true — excluded from distribution
        ssh_authorize_extra:
          - name: backup-host
            identity_file: id_ed25519_backup
```

After this role runs:
- `server1` and `server2` will have `marcus`'s `id_ed25519_server.pub` in their
  `authorized_keys`
- `backup-host` will have `marcus`'s `id_ed25519_backup.pub`
- `work-laptop` is untouched (no `ssh_authorize: true`)

### With controller authorization

```yaml
- hosts: servers
  become: true
  roles:
    - role: marcus_grant.dotfiles.ssh_authorize
      vars:
        ssh_authorize_owner: marcus
        ssh_config_entries:
          - name: server1
            ssh_authorize: true
        ssh_authorize_controller_user: ansible_runner
        ssh_authorize_controller_identity_file: id_ed25519_controller
```

`server1` gets `marcus`'s `id_ed25519.pub`. The controller user `ansible_runner`
gets `marcus`'s `id_ed25519_controller.pub` — enabling `marcus@server1` to SSH
back to the controller.

## Playbook Integration

### Version

Introduced in `marcus_grant.dotfiles` **1.13.0**. Controller authorization
added in **1.14.0**.

### Installation

```bash
ansible-galaxy collection install marcus_grant.dotfiles:>=1.14.0
```

### Force-replace a stale key

When a keypair has been regenerated and the old pubkey needs replacing:

```bash
ansible-playbook site.yml -e ssh_authorize_force=true
```

This is intentionally not automated — overwriting authorized keys requires
explicit operator intent.

## License

GPL-2.0-or-later

## Author Information

Marcus Grant
[marcusfg@protonmail.com](mailto:marcusfg@protonmail.com)
[github.com/marcus-grant](https://github.com/marcus-grant)

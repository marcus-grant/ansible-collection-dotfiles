# marcus_grant.dotfiles.ssh_authorize

Distributes SSH public keys to `authorized_keys` on destination hosts, brokered
entirely by the Ansible controller. The source host's pubkeys are slurped by the
controller and written to each destination via `delegate_to` — no direct
source→destination SSH connectivity is required.

Optionally also writes the source host's pubkey into the **controller's** own
`authorized_keys`, enabling the source to SSH back into the controller.

## Status: Not Production-Ready

This role has known reliability issues on non-standard targets. Do not use in
production without reading the Known Issues section below.

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
| `ssh_config_common_entries` | no | `[]` | Destination entries (common to all hosts), filtered to those with `ssh_authorize: true`. Mirrors the shape of `ssh_config` common entries. |
| `ssh_config_host_entries` | no | `[]` | Destination entries (per-host), filtered to those with `ssh_authorize: true`. Mirrors the shape of `ssh_config` host entries. |
| `ssh_authorize_extra` | no | `[]` | Additional destination entries not covered by `ssh_config_common_entries`/`ssh_config_host_entries`. Same format, no filtering — all entries are processed. |
| `ssh_authorize_force` | no | `false` | When `true`, uses regexp-based matching on key-type + comment to replace a stale key line in `authorized_keys`. When `false`, exact-line match is used (no-op if already present). **Never set in vars files — pass as `-e ssh_authorize_force=true`.** |
| `ssh_authorize_controller_user` | no | — | When defined, authorizes the source host's pubkey(s) into this user's `authorized_keys` on the Ansible controller. Acts as the feature enabler — if unset, the entire controller block is skipped. Resolved via `getent passwd` delegated to `localhost`. |
| `ssh_authorize_controller_identity_file` | no | — | When set alongside `ssh_authorize_controller_user`, only this key (filename stem, no `.pub`) is pushed to the controller instead of all already-slurped pubkeys. The key is slurped directly from the source host — it need not appear in any destination entry. Requires `ssh_authorize_controller_user`. |

### Destination entry format

Both `ssh_config_common_entries`/`ssh_config_host_entries` and `ssh_authorize_extra` accept entries with:

| Key | Required | Default | Description |
|---|---|---|---|
| `host` | **yes** | — | Ansible inventory hostname of the destination. Used as `delegate_to` target. |
| `identity_file` | no | `id_ed25519` | Filename stem, tilde path (`~/.ssh/id_ed25519`), or absolute path of the keypair. The basename is extracted internally and `.pub` is appended. Matches the verbatim path used in `ssh_config` entries. |
| `ssh_authorize` | no | — | Set to `true` to include this entry when sourced from `ssh_config_common_entries`/`ssh_config_host_entries`. Entries without this key, or with `false`, are filtered out. |
| `home` | no | resolved via `getent passwd` | Absolute path to the destination user's home directory. Skips the delegated `getent` lookup — required for hosts without `getent` (e.g. appliances with restricted shells such as OPNsense/FreeBSD). |

## Topology resolution

1. `ssh_config_common_entries` and `ssh_config_host_entries` are concatenated
   and filtered to entries where `ssh_authorize: true` is explicitly set.
   Absent or `false` → excluded.
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
        ssh_config_host_entries:
          - host: server1
            identity_file: id_ed25519_server
            ssh_authorize: true
          - host: server2
            ssh_authorize: true
          - host: work-laptop
            # no ssh_authorize: true — excluded from distribution
        ssh_authorize_extra:
          - host: backup-host
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
        ssh_config_host_entries:
          - host: server1
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
added in **1.14.0**. Optional `home` override for destination entries added in **1.14.3**.

### Installation

```bash
ansible-galaxy collection install marcus_grant.dotfiles:>=1.14.3
```

### Force-replace a stale key

When a keypair has been regenerated and the old pubkey needs replacing:

```bash
ansible-playbook site.yml -e ssh_authorize_force=true
```

This is intentionally not automated — overwriting authorized keys requires
explicit operator intent.

## Known Issues

### 1. Module execution fails on appliance targets (FreeBSD / OPNsense)

Ansible module execution exits 127 on these targets despite Python being
present and `PATH` correct when tested interactively. Root cause is under
investigation — likely Ansible's module-path setup, shebang resolution, or
`tmpdir` restrictions imposed by the restricted shell. Until resolved, this
role cannot be used against appliance-class hosts.

### 2. Home override (v1.14.3) does not fix appliance targets

The `home:` key on a destination entry skips the delegated `getent` lookup,
but all subsequent tasks (`ansible.builtin.file`, `ansible.builtin.lineinfile`)
still execute on the destination host. Appliances fail at the same exit-127
root cause one task later. The override only helps hosts that have `getent`
absent but otherwise support full Ansible module execution — an uncommon
combination.

### 3. Force mode does not work for 2-field keys

`ssh_authorize_force: true` uses a regexp on `^type .* comment$`, which is
only valid when the key has a comment field (3 space-separated tokens). Keys
with 2 fields (type + key body, no comment) fall back to exact-line match,
meaning a stale 2-field key is never replaced. This is a silent no-op — no
error is raised.

### 4. Design assumes a Python interpreter on every destination

The role uses `ansible.builtin.file` and `ansible.builtin.lineinfile`, which
require Ansible's full module-execution stack on every destination host. This
fails for exactly the category of hosts most likely to need opt-in key
distribution — routers, appliances, and embedded systems. Candidate fix:
switch to `ansible.posix.authorized_key` to reduce the execution surface, or
use `ansible.builtin.raw` / `shell` for the write step.

### 5. Role may be archived

Given issues 1–4, the role is being evaluated for either a significant
redesign or archival. If archived, a replacement approach (direct use of
`ansible.posix.authorized_key` in plays, or a new role built around it) will
be documented here.

## License

GPL-2.0-or-later

## Author Information

Marcus Grant
[marcusfg@protonmail.com](mailto:marcusfg@protonmail.com)
[github.com/marcus-grant](https://github.com/marcus-grant)

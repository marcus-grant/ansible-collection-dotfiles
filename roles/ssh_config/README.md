# ssh_config

Manages `~/.ssh/config` using a drop-in directory pattern. Each host entry gets
its own file in `~/.ssh/config.d/`. The main `~/.ssh/config` contains only an
`Include` directive — unmanaged files in `config.d/` are never touched. Stale
`managed-*.conf` files are removed when entries are dropped from the variable lists.

## Role Variables

| Variable | Default | Description |
|---|---|---|
| `ssh_config_owner` | `{{ ansible_user_id }}` | User who owns the SSH config files |
| `ssh_config_common_entries` | `[]` | Shared host entries (e.g. from `group_vars`) |
| `ssh_config_host_entries` | `[]` | Per-host entries (e.g. from `host_vars`) |
| `ssh_config_defaults` | `{}` | Global SSH options rendered as `Host *` block in `zz-managed-defaults.conf` |
| `ssh_config_known_hosts` | `[]` | Static known_hosts key strings added via `lineinfile` |

The role concatenates `ssh_config_common_entries + ssh_config_host_entries` before
rendering. Common entries appear first (SSH first-match-wins).

## Entry Shape

Every entry must have a `host` key. All other keys use **snake_case**, where each
underscore-delimited segment maps to one PascalCase word in the rendered directive:

```
host_name    → HostName
identity_file → IdentityFile
host_based_authentication → HostBasedAuthentication
```

Values render **verbatim** — use full paths where the SSH client expects them:

```yaml
ssh_config_common_entries:
  - host: github.com           # required
    user: git
    identity_file: ~/.ssh/id_ed25519_git   # full path, rendered as-is

ssh_config_host_entries:
  - host: myserver
    host_name: 192.168.1.10    # host_name → HostName
    user: marcus
    port: 2222
    identity_file: ~/.ssh/id_ed25519_personal
    ssh_authorize: true        # reserved — passed through to ssh_authorize role, not rendered
```

The `ssh_authorize` key is excluded from rendering. It is reserved for the
`ssh_authorize` role, which reads it to determine where to distribute public keys.

`ssh_config_defaults` keys follow the same snake_case convention:

```yaml
ssh_config_defaults:
  add_keys_to_agent: "yes"    # → AddKeysToAgent yes
  identities_only: "yes"      # → IdentitiesOnly yes
  server_alive_interval: 60   # → ServerAliveInterval 60
```

## File Layout on Target

```
~/.ssh/
├── config                          ← Include ~/.ssh/config.d/* only
├── config.d/
│   ├── managed-github.com.conf     ← one file per entry
│   ├── managed-myserver.conf
│   └── zz-managed-defaults.conf   ← Host * block, sorts last
└── known_hosts
```

`zz-` prefix ensures `Host *` sorts after all `managed-*.conf` files so that
specific host entries always take precedence.

## Example

```yaml
ssh_config_owner: marcus

ssh_config_common_entries:
  - host: github.com
    user: git
    identity_file: ~/.ssh/id_ed25519_git

ssh_config_host_entries:
  - host: myserver
    host_name: 192.168.1.10
    user: marcus
    port: 2222
    identity_file: ~/.ssh/id_ed25519_personal
    ssh_authorize: true

ssh_config_defaults:
  add_keys_to_agent: "yes"
  identities_only: "yes"
  server_alive_interval: 60

ssh_config_known_hosts:
  - "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
```

Produces `~/.ssh/config`:

```
# Ansible managed - do not edit
Include ~/.ssh/config.d/*
```

Produces `~/.ssh/config.d/managed-github.com.conf`:

```
# Ansible managed - do not edit

Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_git
```

Produces `~/.ssh/config.d/managed-myserver.conf`:

```
# Ansible managed - do not edit

Host myserver
  HostName 192.168.1.10
  User marcus
  Port 2222
  IdentityFile ~/.ssh/id_ed25519_personal
```

Produces `~/.ssh/config.d/zz-managed-defaults.conf`:

```
# Ansible managed - do not edit

Host *
  AddKeysToAgent yes
  IdentitiesOnly yes
  ServerAliveInterval 60
```

## Role Pipeline

```
profile → userdirs → zsh → ssh_keys → ssh_config → neovim → ...
```

Key files referenced in `identity_file` are expected to already exist (deployed
by the `ssh_keys` role). This role has no hard dependency on `ssh_keys`.

## Dependencies

None.

## Tested Platforms

- Debian 12 (bookworm)
- Arch Linux

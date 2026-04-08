# ssh_config

Templates `~/.ssh/config` from lists of host entries. Manages `.ssh/` directory
permissions and optional `known_hosts` static entries.

## Role Variables

| Variable | Default | Description |
|---|---|---|
| `ssh_config_owner` | `{{ ansible_user_id }}` | User who owns the SSH config |
| `ssh_config_common_entries` | `[]` | Shared host entries (e.g. from `group_vars`) |
| `ssh_config_host_entries` | `[]` | Per-host entries (e.g. from `host_vars`) |
| `ssh_config_defaults` | `{}` | Global SSH options rendered as `Host *` block (appended last) |
| `ssh_config_known_hosts` | `[]` | Static known_hosts key strings added via `lineinfile` |

The role concatenates `ssh_config_common_entries + ssh_config_host_entries`
before rendering. Common entries appear first in the config (first-match-wins).

### Entry shape

Both lists accept entries with these keys:

```yaml
- host: github.com          # required — SSH Host pattern
  user: git                 # optional — User directive
  identity_file: id_ed25519 # optional — IdentityFile ~/.ssh/<value>
  hostname: 192.168.1.10    # optional — HostName directive
  port: 22                  # optional — Port directive
  authorize: true           # optional — reserved for ssh_authorize role, ignored here
```

### Example

```yaml
ssh_config_owner: marcus

ssh_config_common_entries:
  - host: github.com
    user: git
    identity_file: id_ed25519_git

ssh_config_host_entries:
  - host: myserver
    hostname: 192.168.1.10
    user: marcus
    port: 2222
    identity_file: id_ed25519_personal
    authorize: true

ssh_config_defaults:
  AddKeysToAgent: "yes"
  IdentitiesOnly: "yes"
  ServerAliveInterval: 60

ssh_config_known_hosts:
  - "github.com ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIOMqqnkVzrm0SdG6UOoqKLsabgH5C9okWi0dh2l9GKJl"
```

Produces `~/.ssh/config`:

```
# Ansible managed - do not edit

Host github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_git

Host myserver
  HostName 192.168.1.10
  User marcus
  Port 2222
  IdentityFile ~/.ssh/id_ed25519_personal

Host *
  AddKeysToAgent yes
  IdentitiesOnly yes
  ServerAliveInterval 60
```

## Role Pipeline

```
profile → userdirs → zsh → ssh_keys → ssh_config → neovim → ...
```

This role assumes key files referenced in `identity_file` already exist on the
target (deployed by the `ssh_keys` role). It has no hard dependency on `ssh_keys`.

The `authorize` flag on entries is reserved for the future `ssh_authorize` role,
which will use it to determine where to distribute public keys. This role ignores it.

## Dependencies

None.

## Tested Platforms

- Debian 12 (bookworm)
- Arch Linux

# gpg_transfer

Transfer existing GPG key material from an Ansible controller to target hosts.
Enables targets to use the operator's GPG identity for tools that depend on it
(e.g. `pass`, git signing). This role transports key material — it does not manage
keys. Key management (trust decisions, passphrase handling, teardown of superseded
keys) is the operator's responsibility.

## Trust Model

**This role assumes the target host is trusted with private key material.**
Transport is over an already-authenticated SSH channel. The operator is responsible
for ensuring the target host is under their control before running this role.
This assumption must be understood before use.

## Passphrase Contract

`gpg_transfer_passphrase` must be populated via `vars_prompt` (masked input) or
an equivalent secure, non-persisted exchange. **Storing GPG passphrases in vault
or variable files is explicitly discouraged and unsupported.** The role is designed
for interactive use at provisioning time with the operator at the keyboard.

## Fingerprint Sensitivity

Fingerprints are not secret cryptographic material, but they can link identities.
Operators with pseudonymous concerns should define fingerprint variables in vault
rather than in plaintext variable files or play arguments.

## Requirements

- `gpg` must be installed on the **controller** (the machine running Ansible).
- The role installs `gnupg` and `pinentry` on targets automatically.
- `/dev/shm` (tmpfs) must be available on both controller and target (standard on Linux).

## Out of Scope

- Key generation
- Key trust establishment
- `pass` installation (belongs to the `pass_store` role)
- Passphrase storage or management

## Role Variables

### Required

| Variable | Description |
|---|---|
| `gpg_transfer_owner` | Target user who owns the gnupg directory and keyring |
| `gpg_transfer_passphrase` | Controller key passphrase — only required when transfer is needed |

### Key Selection

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_keys` | `"all"` | `"all"` or list of `{fingerprint, export_mode}` dicts |
| `gpg_transfer_default_export_mode` | `"full"` | `"full"` or `"subkeys"` — applies when `gpg_transfer_keys` is `"all"` or list entry omits `export_mode` |

When `gpg_transfer_keys` is `"all"`, every secret key on the controller is transferred.
When a list, each entry must have a `fingerprint` field and may have an `export_mode` field:

```yaml
gpg_transfer_keys:
  - fingerprint: "ABCD1234..."
    export_mode: "full"       # gpg --export-secret-keys
  - fingerprint: "EFGH5678..."
    export_mode: "subkeys"    # gpg --export-secret-subkeys
```

### Controller

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_controller_host` | `localhost` | Ansible host that holds the GPG keys. `localhost` means the Ansible control node. Override in molecule or multi-host setups where a dedicated container holds the keys. |
| `gpg_transfer_controller_gnupghome` | `~/.gnupg` | gnupg home on the controller host (expanded via `getent passwd` on that host) |

### Paths

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_gnupghome` | `~/.gnupg` | Target-side gnupg directory (expanded via `getent passwd`) |

### Symlink

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_create_symlink` | `false` | When `true` and `gpg_transfer_gnupghome` differs from `~/.gnupg`, create `~/.gnupg` as a symlink pointing to `gpg_transfer_gnupghome` |

If `~/.gnupg` already exists as a real directory, the role **fails** — manual
intervention is required. The role will not clobber existing directories.

### Agent Configuration

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_agent_config` | see below | Dict rendered into `gpg-agent.conf` on the target |

Default agent config:

```yaml
gpg_transfer_agent_config:
  pinentry-program: "/usr/bin/pinentry-curses"
  allow-loopback-pinentry: true
```

Boolean `true` values render as bare directives (no `=` or value). String values
render as `key value`. Override in `host_vars` or `group_vars` as needed.

### Ownertrust and gpg.conf

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_ownertrust` | `true` | Export and import the controller's ownertrust database |
| `gpg_transfer_gpg_conf` | `true` | Copy controller's `gpg.conf` to target's gnupg home |

An `ownertrust.txt` file is written alongside the keyring as an Ansible change-detection
artifact. GPG ignores it — it will not affect keyring operation.

### Verification and Idempotency

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_verify` | `true` | Post-transfer fingerprint verification — mismatch is a hard fail |

Before any transfer, the role compares fingerprints already present on the target
against the requested set. Only the diff is transferred. When no transfer is needed,
no passphrase is prompted, no secret material is in transit, and the role is fully
unattended.

Set `gpg_transfer_verify: false` to skip post-transfer verification on re-runs where
a downstream role (e.g. `pass_store`) provides functional verification.

### Packages

| Variable | Default | Description |
|---|---|---|
| `gpg_transfer_extra_packages` | `[]` | Additional packages appended to the distro-specific list |

## Example Playbook

```yaml
- hosts: workstations
  vars_prompt:
    - name: gpg_transfer_passphrase
      prompt: "GPG key passphrase"
      private: true
  roles:
    - role: marcus_grant.dotfiles.gpg_transfer
      vars:
        gpg_transfer_owner: "{{ ansible_user }}"
        gpg_transfer_keys: "all"
        gpg_transfer_ownertrust: true
        gpg_transfer_gpg_conf: true
```

Selective transfer with subkeys-only for a specific key:

```yaml
- hosts: workstations
  vars_prompt:
    - name: gpg_transfer_passphrase
      prompt: "GPG key passphrase"
      private: true
  roles:
    - role: marcus_grant.dotfiles.gpg_transfer
      vars:
        gpg_transfer_owner: "{{ ansible_user }}"
        gpg_transfer_keys:
          - fingerprint: "ABCDEF1234567890..."
            export_mode: "full"
          - fingerprint: "FEDCBA0987654321..."
            export_mode: "subkeys"
        gpg_transfer_agent_config:
          pinentry-program: "/usr/bin/pinentry-gnome3"
          allow-loopback-pinentry: true
        gpg_transfer_extra_packages:
          - pinentry-gnome3
```

## Dependencies

None. `pass_store` soft-depends on GPG state created by this role (documented in
`pass_store` meta and README).

## License

GPL-2.0-or-later

## Author

Marcus Grant (marcusfg@protonmail.com)

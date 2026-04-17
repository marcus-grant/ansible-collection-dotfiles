# password_store

Clones an existing git-backed [pass](https://www.passwordstore.org/) store to target hosts. The store must already exist and be accessible via the provided git URL. This role only deploys — it does not initialise or manage the store contents.

## Requirements

- `community.general` collection (for Archlinux package management via `pacman` module)
- The `git` binary will be installed by this role
- The `git` role (`marcus_grant.dotfiles.git`) is recommended for full git configuration but is not a hard dependency — `password_store` only needs the binary

## Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `password_store_owner` | yes | — | Target user who owns the store |
| `password_store_repo` | yes | — | Git remote URL for the existing store |
| `password_store_dir` | no | `~/.password-store` | Clone destination (tilde expanded relative to owner home) |
| `password_store_controller_host` | no | `localhost` | Host to delegate preflight checks to |
| `password_store_preflight_check` | no | `true` | Run preflight checks on the controller store before deploying |
| `password_store_profile_dropin` | no | `false` | Write a profile drop-in exporting `PASSWORD_STORE_DIR` |
| `password_store_profile_dropin_dir` | no | `{{ profile_d_path \| default('~/.config/profile.d') }}` | Directory to write the drop-in into |
| `password_store_profile_dropin_order` | no | `"53"` | Numeric load-order prefix for the drop-in filename |
| `password_store_verify_entry` | no | `""` | Run `pass show <entry>` after deployment to verify decryption works |
| `password_store_extra_packages` | no | `[]` | Additional packages to install alongside `pass` |

## Behaviour

**Default path** (`password_store_dir: ~/.password-store`): clones directly to the standard pass location. No symlink needed.

**Custom path, no drop-in**: clones to the custom path and creates a symlink at `~/.password-store` pointing to it.

**Custom path, drop-in enabled**: clones to the custom path and writes `<order>-managed-password_store.sh` to `password_store_profile_dropin_dir` exporting `PASSWORD_STORE_DIR`. No symlink created.

## Preflight checks

When `password_store_preflight_check: true` (default), the role delegates to `password_store_controller_host` and verifies:
- The controller store has no uncommitted changes
- The controller store has no unpushed commits

All preflight tasks use `no_log: true` — pass output contains password entry paths.

## Example

```yaml
- hosts: workstations
  roles:
    - role: marcus_grant.dotfiles.password_store
      vars:
        password_store_owner: alice
        password_store_repo: "git@github.com:alice/pass-store.git"
        password_store_dir: "~/.local/share/pass"
        password_store_profile_dropin: true
```

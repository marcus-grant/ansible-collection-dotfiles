# marcus_grant.dotfiles.zsh

Installs ZSH, clones a dotfiles git repository, places shell config shims at
the locations ZSH expects them, and optionally sets ZSH as the default shell.

## Requirements

### System dependencies (non-Ansible)

- **`git`** must be present on the target host before this role runs.
  It is not installed by this role. Ensure it is available via a prior role
  (e.g. `marcus_grant.dev.git`) or a pre-task.
- **`ssh_config`** role must have run before this role if `zsh_git_repo` is an
  SSH URL — the `dotfiles_git` module enforces this with a pre-flight check that
  fails fast with a clear error rather than hanging on an SSH prompt.

## Role Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `zsh_owner` | no | `{{ ansible_user_id }}` | User who owns the config files and receives the default shell change |
| `zsh_git_repo` | yes | — | Git URL or path of the ZSH dotfiles repo. Supports HTTPS and SSH URLs; SSH triggers pre-flight check (requires `ssh_config` role). |
| `zsh_config_dest` | no | `~/.config/zsh` | Clone destination for the dotfiles repo (`~` resolved against `zsh_owner`'s home) |
| `zsh_rc_file` | no | `rc.zsh` | File inside repo to shim as `~/.zshrc` |
| `zsh_env_file` | no | `env.zsh` | File inside repo to shim as `~/.zshenv` |
| `zsh_profile_file` | no | `profile.zsh` | File inside repo to shim as `~/.zprofile` |
| `zsh_env_source_profile` | no | `true` | Prepend `source $HOME/.profile` in `~/.zshenv` shim |
| `zsh_git_version` | no | `HEAD` | Branch, tag, or commit to check out |
| `zsh_git_force` | no | `false` | Re-clone even if destination already exists |
| `zsh_git_update` | no | `false` | Pull latest commits on each run; reports `changed` if new commits fetched |
| `zsh_shell_as_default` | no | `false` | Set ZSH as the login shell for the ansible user |
| `zsh_default_shell_path` | no | `/usr/bin/zsh` | ZSH binary path used when setting default shell |
| `zsh_extra_packages` | no | `[]` | Additional packages to install alongside ZSH |

## Dependencies

- `marcus_grant.dotfiles.profile` — run before this role to ensure `~/.profile`
  exists for the `zshenv` shim to source.

Soft dependency: `ssh_config` role must have run before this role when
`zsh_git_repo` is an SSH URL.

## Example Playbook

```yaml
- hosts: workstations
  roles:
    - role: marcus_grant.dotfiles.zsh
      vars:
        zsh_git_repo: https://github.com/yourname/dots-zsh
        zsh_shell_as_default: true
```

## License

GPL-2.0-or-later

## Author Information

Marcus Grant
[marcusfg@protonmail.com](mailto:marcusfg@protonmail.com)
[github.com/marcus-grant](https://github.com/marcus-grant)

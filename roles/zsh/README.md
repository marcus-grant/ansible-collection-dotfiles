# marcus_grant.dotfiles.zsh

Installs ZSH, clones a dotfiles git repository, places shell config shims at
the locations ZSH expects them, and optionally sets ZSH as the default shell.

## Requirements

### System dependencies (non-Ansible)

- **`git`** must be present on the target host before this role runs.
  It is not installed by this role. Ensure it is available via a prior role
  (e.g. `marcus_grant.dev.git`) or a pre-task.

## Role Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `zsh_git_repo` | yes | — | Git URL or path of the ZSH dotfiles repo. Supports HTTPS and SSH URLs; SSH requires keys configured on the target host. |
| `zsh_config_dest` | no | `~/.config/zsh` | Clone destination for the dotfiles repo |
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

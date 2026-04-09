# Git Role — `marcus_grant.dotfiles`

Install git and configure global git settings (user identity, default branch,
pull behavior) for a specified system user.

## Requirements

The `community.general` collection must be installed:

```yaml
collections:
  - name: community.general
```

## Role Variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `git_owner` | string | — | yes | System username to configure git for. Home resolved via `getent`. |
| `git_user_name` | string | — | yes | Value for `user.name` in global git config. |
| `git_user_email` | string | — | yes | Value for `user.email` in global git config. |
| `git_extra_packages` | list | `[]` | no | Additional packages to install alongside git (e.g. `git-lfs`, `git-crypt`, `lazygit`). |
| `git_default_branch` | string | `main` | no | Value for `init.defaultBranch` in global git config. |
| `git_pull_rebase` | bool | `false` | no | Value for `pull.rebase` in global git config. Written as `true`/`false` (lowercase). |
| `git_config_extra` | list | `[]` | no | Additional global git config entries. List of `{prop: "section.option", value: "..."}` dicts. |

### Notes

`git_config_extra` entries use the dotted `section.option` format for `prop`, matching
`git config --global` key syntax. Example:

```yaml
git_config_extra:
  - {prop: "core.autocrlf", value: "false"}
  - {prop: "push.autoSetupRemote", value: "true"}
```

## Example Playbook

```yaml
- hosts: workstations
  roles:
    - role: marcus_grant.dotfiles.git
      vars:
        git_owner: marcus
        git_user_name: Marcus Grant
        git_user_email: marcus@example.com
        git_default_branch: main
        git_pull_rebase: true
        git_extra_packages:
          - git-lfs
        git_config_extra:
          - {prop: "core.autocrlf", value: "false"}
```

## Soft Dependencies

None. This role does not clone any repositories, so `ssh_config` is not required.
If you later use git over SSH in another role, run `ssh_config` before that role.

## License

GPL-2.0-or-later

## Author

Marcus Grant — [marcusgrant.me](https://marcusgrant.me)

# Pyenv Role — `marcus_grant.dotfiles`

Install pyenv via git clone, compile Python versions from source, set a global
version, and configure shell integration via a profile.d drop-in script.

## Requirements

None beyond a supported OS. Build dependencies are installed automatically.

## Role Variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `pyenv_owner` | string | — | yes | System user to install pyenv for. Home resolved via `getent`. |
| `pyenv_versions` | list | — | yes | Python version strings to compile and install (e.g. `["3.12.0"]`). |
| `pyenv_global` | string | — | yes | Version to set as global default. Must be in `pyenv_versions`. |
| `profile_d_path` | string | — | yes | Directory for the shell integration drop-in. Provided by the `profile` role. |
| `pyenv_root` | string | `~/.local/share/pyenv` | no | pyenv installation directory. `~` expanded against the owner's home. |
| `pyenv_update` | bool | `false` | no | Pull latest pyenv on each run when `true`. |
| `pyenv_repo` | string | `https://github.com/pyenv/pyenv.git` | no | Clone source for pyenv. |

## Example Playbook

```yaml
- hosts: workstations
  roles:
    - role: marcus_grant.dotfiles.profile
      vars:
        profile_user: marcus
        profile_group: marcus
        profile_home: /home/marcus
        profile_d_path: /home/marcus/.config/profile.d

    - role: marcus_grant.dotfiles.pyenv
      vars:
        pyenv_owner: marcus
        pyenv_versions:
          - "3.12.0"
          - "3.11.9"
        pyenv_global: "3.12.0"
        profile_d_path: /home/marcus/.config/profile.d
```

## Soft Dependencies

This role has a soft dependency on `marcus_grant.dotfiles.profile`. The `profile`
role creates `profile_d_path` and sources all scripts within it at login. If you
run `pyenv` without `profile` first, you must create `profile_d_path` yourself
and ensure it is sourced by the shell.

## License

GPL-2.0-or-later

## Author

Marcus Grant — [marcusgrant.me](https://marcusgrant.me)

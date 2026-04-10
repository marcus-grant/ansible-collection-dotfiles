# Pip Role — `marcus_grant.dotfiles`

Ensure pip is available for a given Python interpreter, install pip packages
(including optionally pipx), install pipx packages, and configure shell
environment via an optional profile.d drop-in.

## Requirements

None beyond a supported OS. System pip is installed automatically when not using pyenv.

## Role Variables

| Variable | Type | Default | Required | Description |
|---|---|---|---|---|
| `pip_owner` | string | — | yes | System user to install packages for. Home resolved via `getent`. |
| `pip_python` | string | auto | no | Python interpreter path. Defaults to `pyenv_root_abs/shims/python` if `pyenv_root_abs` is defined (set by pyenv role), otherwise `/usr/bin/python3`. |
| `pip_packages` | list | `[]` | no | Pip packages to install. Supports version syntax (`httpie==3.2.0`). |
| `pip_install_pipx` | bool | `false` | no | Explicitly install pipx even when `pipx_packages` is empty. Pipx is always installed automatically when `pipx_packages` is non-empty. |
| `pipx_packages` | list | `[]` | no | Pipx packages to install. pipx is installed automatically — no need to add it to `pip_packages`. |
| `pipx_default_python` | string | `{{ pip_python }}` | no | Python interpreter for pipx to use when creating package environments. |
| `pipx_bin_dir` | string | `~/.local/bin` | no | Directory pipx installs entry-point scripts into. `~` expanded against the owner's home. |
| `profile_d_path` | string | — | no | If defined, a `pip.sh` drop-in is written here exporting `PIPX_DEFAULT_PYTHON`, `PIPX_BIN_DIR`, and prepending `pipx_bin_dir` to `PATH`. Provided by the `profile` role. |

## Example Playbook

### With pyenv (recommended)

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
        pyenv_versions: ["3.12.0"]
        pyenv_global: "3.12.0"
        profile_d_path: /home/marcus/.config/profile.d

    - role: marcus_grant.dotfiles.pip
      vars:
        pip_owner: marcus
        pip_packages:
          - pipx
          - httpie
        pipx_packages:
          - cowsay
        profile_d_path: /home/marcus/.config/profile.d
```

### System Python only

```yaml
- hosts: workstations
  roles:
    - role: marcus_grant.dotfiles.pip
      vars:
        pip_owner: marcus
        pip_packages:
          - httpie
```

## Soft Dependencies

- `marcus_grant.dotfiles.pyenv` — optional. When the pyenv role runs earlier in the
  play, it sets `pyenv_root_abs` which this role uses to select the pyenv shim as the
  interpreter and skip system pip installation.
- `marcus_grant.dotfiles.profile` — optional. Provides `profile_d_path` and sources
  all drop-ins at login. Required if you want automatic shell integration.

## License

GPL-2.0-or-later

## Author

Marcus Grant — [marcusgrant.me](https://marcusgrant.me)

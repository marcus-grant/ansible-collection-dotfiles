# Neovim Role — `marcus_grant.dotfiles`

Install neovim and clone a git-controlled config repo to `~/.config/nvim`
using the `dotfiles_git` module. Supports package manager and appimage
install methods.

## Requirements

- `git` on the target host
- `ssh_config` role applied before this role if `neovim_git_repo` is an SSH URL —
  the `dotfiles_git` module checks that `known_hosts` and SSH config are in place
  and fails fast with a clear error if they are not

## Role Variables

| Variable | Default | Comments |
| -------- | ------- | -------- |
| `neovim_owner` | `{{ ansible_user_id }}` | User who owns the config and binary |
| `neovim_install_method` | `package` | `package` or `appimage` |
| `neovim_extra_packages` | `[]` | Extra packages installed alongside neovim (e.g. ripgrep, tree-sitter) |
| `neovim_git_repo` | `""` | SSH or HTTPS URL of the neovim config repo. Clone is skipped if empty. |
| `neovim_git_version` | `main` | Branch, tag, or commit to check out |
| `neovim_git_update` | `false` | Pull on subsequent runs when `true` |
| `neovim_appimage_version` | `v0.12.1` | Version string to download and version-check against |
| `neovim_appimage_dest` | `~/.local/bin` | Directory to place the appimage binary (`~` expands to `neovim_owner`'s home) |
| `neovim_appimage_name` | `nvim` | Filename of the placed binary |
| `neovim_appimage_url` | GitHub releases URL | Override to use a local or mirror URL (useful in tests) |
| `neovim_alt_pkg` | `""` | Override the package name for the `package` install method |

### Notes

- `neovim_git_repo`: required for config clone. Use an SSH URL when the
  target has a key deployed; HTTPS for public repos.
- `neovim_git_update`: set to `true` only if you want the role to pull
  new commits on every run. Defaults to `false` to treat the clone as a
  versioned install.
- `neovim_appimage_url`: defaults to the GitHub releases template using
  `neovim_appimage_version`. Override in tests or to use a mirror:
  ```yaml
  neovim_appimage_url: file:///opt/local-nvim.appimage
  ```
- AppImage install requires FUSE on the target. FUSE packages installed
  automatically: `libfuse2` (Debian), `fuse2` (Arch). The binary itself
  is NOT executed by the role — FUSE is only needed when you run nvim.

## Example Playbook

```yaml
- hosts: workstations
  roles:
    - role: marcus_grant.dotfiles.neovim
      vars:
        neovim_owner: marcus
        neovim_install_method: appimage
        neovim_appimage_version: v0.12.1
        neovim_git_repo: git@github.com:marcus-grant/dots-neovim.git
        neovim_git_version: main
        neovim_extra_packages:
          - ripgrep
          - fd
          - tree-sitter
```

## Dependencies

None hard dependencies. Soft dependency: `ssh_config` role must have run before
this role when `neovim_git_repo` is an SSH URL.

## License

GPL-2.0-or-later

## Author

Marcus Grant — [marcusgrant.me](https://marcusgrant.me)

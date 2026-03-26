# TODO

## TDD Rules — always enforced, never deleted

- No code change without a failing test first
- One role at a time: `molecule create` → `molecule converge` → `molecule verify` → `molecule destroy` → commit
- Commits must be logical, minimal, and easy to review — no batching unrelated changes
- Delete completed items from this file entirely before committing — no strikethrough, no "done" markers, no traces

---

## Molecule tests — add Arch Linux platform, fix existing bugs

Each role: add `Dockerfile-archlinux.j2` + Arch platform to `molecule.yml`, fix any bugs in `converge.yml`/`verify.yml` for all platforms, write Arch-specific verify checks under `when: inventory_hostname == 'archlinux'`.

### `userdirs`
- Files: add `Dockerfile-archlinux.j2`; update `molecule.yml`, `converge.yml`, `verify.yml`
- Bug: converge + verify both contain copy-pasted zsh content — rewrite both
- converge: run `profile` first (explicit meta dependency), then `userdirs`
- verify: `~/.config/profile.d/10-userdirs.sh` exists mode `0640`; exports XDG vars; XDG dirs exist

### `zsh`
- Files: add `Dockerfile-archlinux.j2`; update `molecule.yml`, `converge.yml`, `verify.yml`
- Bug: verify hardcodes `/root/` paths; checks for symlinks but role templates files
- Bug: missing `profile` pre-run in converge
- converge: run `profile` first; zsh vars: `zsh_git_repo`, `zsh_shell_as_default: true`, `zsh_git_force: true`
- verify: zsh installed; testuser shell is `/usr/bin/zsh`; `~/.config/zsh` is git repo with `dots-zsh` remote; `~/.zshrc`, `~/.zprofile`, `~/.zshenv` exist

### `neovim`
- Files: add `Dockerfile-archlinux.j2`; update `molecule.yml`, `converge.yml`, `verify.yml`
- Bug: converge uses wrong var names (`nvim_git_repo` → `neovim_git_repo`, `nvim_git_force` → `neovim_git_force`, `nvim_appimage`/`nvim_version` don't exist)
- Bug: verify hardcodes `/root/` paths
- converge vars: `neovim_git_repo`, `neovim_git_force: true`, `neovim_install_method: package`
- verify: `nvim --version` exits 0; `~/.config/nvim` exists with `dots-neovim4` remote

### `pip`
- Files: add `Dockerfile-archlinux.j2`; update `molecule.yml`, `converge.yml`, `verify.yml`
- Bug: verify is `assert: true` stub; `pip_package: python3-pip` wrong on Arch (use `python-pip`); tasks lack internal become
- converge: `become: true` at play level; set `pip_package: python-pip`
- verify: `pip3 --version` exits 0; `python3 -m pip --version` exits 0

### `not_coreutil`
- Files: add `Dockerfile-archlinux.j2`; update `molecule.yml`, `converge.yml`, `verify.yml`
- Bug: verify is `assert: true` stub; tasks lack internal become
- converge: `become: true` at play level
- verify: `fd --version`, `rg --version`, `fzf --version` all exit 0

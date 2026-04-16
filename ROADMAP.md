# Roadmap

Items in this file are tracked but not yet scheduled for a release.
Each section lists what is planned, why, and any known constraints.

---

## v2.0.0

Breaking changes held for a major version bump. Coordinate with the collection
rename decision before cutting this release.

### ssh_config: allowlist template refactor

**What:** Invert the blocklist in `roles/ssh_config/templates/ssh_config_entry.j2`
to an explicit allowlist of known SSH config directives. Any entry key not on
the allowlist is silently ignored — it never appears in the rendered file.

**Why:** The current blocklist is brittle. Every new metadata key attached to
shared entries (for consumers like `ssh_authorize`) must be explicitly blocked
or it renders as an invalid SSH directive. The `home` key (v1.14.3) proved this
— it rendered as `Home /tmp/...` and was silently ignored by `ssh`. Future
metadata keys will repeat the bug until the design is inverted.

**Breaking:** Any entry key that currently renders by accident (i.e. not a real
SSH directive) will silently stop rendering. Unlikely to affect correct
playbooks, but it is a behavioral change.

**Constraints:** Do after the collection rename so the major version bump covers
both.

### Collection rename

**What:** Rename `marcus_grant.dotfiles` to a new namespace/name (candidates:
`shell`, `shell_env`). Update all FQCNs, the `galaxy.yml` namespace/name,
any `requirements.yml` references, and re-publish to Ansible Galaxy.

**Why:** The collection has grown beyond "dotfiles" — it now includes SSH key
management, config templating, Python toolchain roles, and an editor role.
The name no longer reflects the scope.

**Constraints:** Namespace/name must be decided before implementation. Galaxy
re-publish requires a new namespace claim if the current namespace changes.

---

## Deferred / Unscoped

Items without a version target. Assigned to the next relevant version once
scoped.

### ssh_authorize: research and decide fate

**Current status:** Not production-ready. Rolled back from infra playbook as
of v1.14.4. Full known issues documented in `roles/ssh_authorize/README.md`.

**Research needed before any redesign or archival decision:**

1. **Exit-127 on FreeBSD / OPNsense appliances.** Module execution fails with
   exit 127 despite Python being present and `PATH` correct interactively.
   Root cause unknown. Reproduce in isolation with `ANSIBLE_DEBUG=1`. Candidate
   causes: Ansible module-path injection, shebang line resolution, `tmpdir`
   restricted by the shell, Python version mismatch.

2. **Force mode broken for 2-field keys.** `ssh_authorize_force: true` falls
   back to exact-line match for keys with no comment field (2 tokens: type +
   key body). Stale 2-field keys are silently left in place. Fix direction:
   regexp matching on key-type + key-body alone, or rethink dedup entirely.

3. **Applicability of `ansible.posix.authorized_key`.** Determine whether
   switching the write step to `ansible.posix.authorized_key` avoids the
   Python module-execution requirement on non-standard destinations, and
   whether it handles all current use cases (explicit home, force mode,
   controller authorization).

**Decision gate:** After research concludes, choose one path:
- **Redesign** around `ansible.posix.authorized_key` if it resolves the
  appliance compatibility issues.
- **Archive** with a clear status note and replacement guidance (direct
  `ansible.posix.authorized_key` usage in plays) if the problems are
  structural.

### dotfiles_owner consolidation

**What:** Each role defines its own `_owner` variable (`ssh_config_owner`,
`userdirs_owner`, `ssh_keygen_owner`, etc.). A collection-level
`dotfiles_owner` default would let plays set one variable instead of repeating
the same value per role.

**Why:** Boilerplate reduction. In practice every role in a play is run for
the same user — the per-role vars are redundant.

**Constraint:** Each role must still accept its own `_owner` var for standalone
use. The collection-level var would be a default-of-defaults, not a replacement.

### Replace community.general.pacman with ansible.builtin.package

**What:** Where `community.general.pacman` is used for Arch Linux package
installs in `prepare.yml` and role tasks, replace with `ansible.builtin.package`
where possible.

**Why:** Reduces the `community.general` dependency surface. `ansible.builtin.package`
is cross-distro and works without extra collections.

**Constraint:** `community.general.pacman`-specific flags (`update_cache`,
`upgrade: true`) have no equivalent in `ansible.builtin.package`. Tasks that
need those flags must stay on `community.general.pacman`.

### SSH negative-path tests for neovim and zsh

**What:** Add `molecule/ssh-negative/` scenario to both `neovim` and `zsh`
roles. Converge with an SSH-format repo URL and `ignore_errors: true`. Verify
that the failure message contains `"SSH not configured for..."` (or equivalent
role-specific message).

**Why:** Both roles support SSH repo URLs but currently have no test confirming
the failure path behaves correctly when SSH is not set up.

### zsh_config_dest README documentation gap

**What:** Document the `~` → `zsh_home` substitution contract for
`zsh_config_dest` in `roles/zsh/README.md`. The variable table currently
omits this behaviour.

**Why:** Users passing `zsh_config_dest: ~/some/path` rely on this substitution
but it is undocumented.

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

### ssh_authorize: investigate exit-127 on FreeBSD / OPNsense appliances

**What:** `ansible` module execution exits 127 on FreeBSD-based appliances
(OPNsense confirmed) despite Python being present and `PATH` correct
interactively.

**Why:** This is the primary blocker preventing `ssh_authorize` from working
against appliance-class hosts — the exact use case the `home:` override was
designed to enable.

**Investigation:** Reproduce in isolation with `ANSIBLE_DEBUG=1`. Candidate
causes: Ansible module-path injection, shebang line resolution, `tmpdir`
location restricted by the shell, or Python version mismatch.

### ssh_authorize: fix force mode for 2-field keys

**What:** `ssh_authorize_force: true` falls back to exact-line match for keys
with no comment field (2 tokens: type + key body). Stale 2-field keys are
silently left in place.

**Why:** Force mode is supposed to replace a stale key regardless of comment.
For commentless keys it does nothing — this is a silent correctness failure.

**Fix direction:** Regexp should match on key-type + key-body alone (no comment
anchor), or the dedup logic should be rethought entirely.

### ssh_authorize: redesign or archive

**What:** Decide whether to redesign the role around `ansible.posix.authorized_key`
(which handles the write step without requiring Python on the destination), or
archive it with a clear status note and replacement guidance.

**Why:** Issues 1–4 in the role's Known Issues section collectively mean the
role is not usable against appliances. The design assumes full Ansible
module-execution on every destination, which fails for the most important
category of targets.

**Decision gate:** Revisit after the exit-127 investigation concludes. If the
root cause is fixable, redesign. If it is structural to how Ansible handles
non-standard targets, archive.

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

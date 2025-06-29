# Ansible Collection Dotfiles - Improvements TODO

This document outlines practical improvements for the `marcus_grant.dotfiles` ansible collection, following conventional Ansible collection patterns.

## Repository Rules & Development Process

### Code Quality Standards
- **All code must pass `ansible-lint` and `yamllint`** - No exceptions
- **Follow Ansible best practices** - Use FQCN, proper variable naming, etc.
- **Keep it simple** - Avoid over-engineering solutions

### Test-Driven Development (TDD) Process
We follow strict TDD practices for all development:

1. **Red Phase** - Write the test first
   - Write a test in `molecule/default/verify.yml` for a specific behavior
   - The test should fail because the implementation doesn't exist
   - Run `molecule verify` to confirm the test fails

2. **Green Phase** - Make it pass
   - Implement the simplest solution that makes the test pass
   - No extra features, just make the test green
   - Run `molecule converge` then `molecule verify` to confirm

3. **Refactor Phase** - Clean it up
   - Consider if the implementation can be improved
   - Reconsider if the spec itself needs adjustment
   - Run `molecule test` to ensure everything still works

4. **Repeat** - Next feature
   - Move to the next spec/feature
   - One behavior at a time

### Example TDD Workflow
```bash
# 1. RED: Write failing test
# Edit roles/example/molecule/default/verify.yml
# Run: cd roles/example && molecule verify
# Confirm it fails

# 2. GREEN: Implement feature
# Edit roles/example/tasks/main.yml
# Run: molecule converge && molecule verify
# Confirm it passes

# 3. REFACTOR: Clean up if needed
# Run: molecule test
# Confirm idempotency and all tests pass
```

### Git Commit Standards
- **Title line**: Max 50 characters
- **Format**: `Prefix: Commit title`
- **Common prefixes**:
  - `Ft:` - Feature addition
  - `Fix:` - Bug fix
  - `Ref:` - Refactoring
  - `Pln:` - Planning/documentation
  - `Tst:` - Test additions/changes
- **Body format**:
  - Use bulleted lists with `*`
  - 2-space indentation for sub-items
  - Max 72 characters per line
  - Parent bullets should be terse
  - Child bullets elaborate on parent

### Example Commit
```
Ft: Add nodejs role with TDD workflow

* Create system-level nodejs/npm installation role
  * Support multiple package managers (apt, dnf, pacman)
  * Allow system-level npm package installation
* Follow strict TDD development process
  * Write tests before implementation
  * Ensure cross-platform compatibility
```

## Overview

The collection has been extracted from a larger ansible playbook monorepo to focus on dotfiles and development environment management. The goal is to create a maintainable collection that's easy to test and deploy locally.

## Current State

- **13 roles** for various dotfile and tool configurations
- **Molecule testing** already setup for most roles (per-role testing)
- **Multi-distro support** (Debian, Ubuntu, Fedora, RedHat, Arch)
- **No collection-level playbook** for easy deployment

## Goals

1. **Keep It Simple**: Follow conventional Ansible collection patterns
2. **Easy Local Deployment**: Create a site.yml that works with external vars
3. **Maintain Quality**: All code passes linters and follows TDD

## High Priority Tasks

### Create Local Deployment Playbook
- [ ] **[HI]** Create `site.yml` at collection root
- [ ] **[HI]** Support external variables from `~/Projects/ops/infra`:
  - [ ] Inventory integration
  - [ ] Group/host vars
  - [ ] Vault files
- [ ] **[HI]** Add useful tags for selective deployment:
  - `shell` - bash, zsh, profile roles
  - `dev` - neovim, vim, tmux roles
  - `tools` - asdf, not_coreutil, pip roles
  - `security` - gpg, pass_store roles
- [ ] **[HI]** Create example playbook showing common use cases

### Create Node.js Role with TDD Workflow
- [ ] **[HI]** Design nodejs role specifications
  - [ ] Install nodejs and npm via system package manager
  - [ ] Support for installing npm packages at system level
  - [ ] Research: npm global install vs distro package manager packages
  - [ ] Research: Best practices for system-level npm package management
- [ ] **[HI]** Implement nodejs role using strict TDD
  - [ ] Create role structure with `ansible-galaxy role init`
  - [ ] Write first test: verify nodejs is installed
  - [ ] Implement nodejs installation for multiple distros
  - [ ] Write test: verify npm is installed and functional
  - [ ] Implement npm installation
  - [ ] Write test: verify specified npm packages are installed
  - [ ] Implement npm package installation (method TBD based on research)
- [ ] **[HI]** Role implementation decisions
  - [ ] Option 1: Always use `npm install -g` for packages
  - [ ] Option 2: Prefer distro packages (e.g., `apt install node-typescript`)
  - [ ] Option 3: Make it configurable per package
  - [ ] Document decision and rationale
- [ ] **[HI]** Test across all supported platforms
  - [ ] Debian/Ubuntu (apt)
  - [ ] RedHat/Fedora (dnf/yum)
  - [ ] Arch (pacman)
  - [ ] Ensure consistent behavior across distros

## Low Priority Tasks

### Add CI/CD with GitHub Actions
- [ ] **[LO]** Create `.github/workflows/ci.yml`
- [ ] **[LO]** Run molecule test for each role on PR/push
- [ ] **[LO]** Use matrix strategy for parallel testing
- [ ] **[LO]** Add ansible-lint and yamllint checks
- [ ] **[LO]** Cache dependencies for faster runs

### Testing Improvements
- [ ] **[LO]** Add molecule test to `profile` role
- [ ] **[LO]** Add basic assertions to existing molecule tests
- [ ] **[LO]** Ensure all roles pass idempotency check

### Documentation
- [ ] **[LO]** Document macOS/Darwin support status per role
- [ ] **[LO]** Add usage examples to main README
- [ ] **[LO]** Document integration with external infra repo

### Cross-Role Variable Sharing Pattern
- [ ] **[LO]** Research Ansible best practices for variable inheritance patterns
  - [ ] Investigate collection-level vs playbook-level variable precedence
  - [ ] Research how other collections handle shared variables
  - [ ] Document findings on variable scoping and precedence
- [ ] **[LO]** Plan implementation approach for XDG variable sharing
  - [ ] Option 1: Use defaults with conditional assignment (`xdg_* | default(profile_xdg_*)`)
  - [ ] Option 2: Task-level variable priority checks
  - [ ] Option 3: Collection-level defaults file pattern
  - [ ] Determine most maintainable approach
- [ ] **[LO]** Implement chosen pattern for XDG variables
  - [ ] Start with `profile` role as pilot
  - [ ] Variables to refactor: `profile_xdg_cache_home`, `profile_xdg_config_home`, etc.
  - [ ] Allow playbook-level `xdg_*` variables to override role-specific ones
- [ ] **[LO]** Test variable inheritance with molecule
  - [ ] Write tests for variable precedence
  - [ ] Ensure backwards compatibility
  - [ ] Test with both role defaults and playbook overrides
- [ ] **[LO]** Extend pattern to other shared variables if successful
  - [ ] Shell environment variables
  - [ ] Tool installation paths
  - [ ] User directory structures

## Implementation Notes

### Variable Sharing Research Notes
Example of the problem:
- Currently: `profile` role has `profile_xdg_cache_home: "{{ ansible_env.HOME }}/.cache"`
- Desired: Check for playbook-level `xdg_cache_home` first, then fall back to role default

Possible implementations to research:
```yaml
# Option 1: In defaults/main.yml
profile_xdg_cache_home: "{{ xdg_cache_home | default(ansible_env.HOME ~ '/.cache') }}"

# Option 2: In tasks/main.yml
- name: Set XDG cache home
  set_fact:
    profile_xdg_cache_home: "{{ xdg_cache_home | default(profile_xdg_cache_home) }}"

# Option 3: Collection-level group_vars/all.yml
xdg_cache_home: "{{ ansible_env.HOME }}/.cache"
# Then roles just use xdg_cache_home directly
```

### site.yml Structure
```yaml
---
- name: Configure dotfiles
  hosts: localhost
  vars_files:
    - "{{ lookup('env', 'HOME') }}/Projects/ops/infra/group_vars/all.yml"
    - "{{ lookup('env', 'HOME') }}/Projects/ops/infra/host_vars/{{ inventory_hostname }}.yml"
  
  tasks:
    - name: Run shell configuration roles
      include_role:
        name: "{{ item }}"
      loop:
        - bash
        - zsh
        - profile
      tags: shell
    
    - name: Run development tool roles
      include_role:
        name: "{{ item }}"
      loop:
        - neovim
        - vim
        - tmux
      tags: dev
```

### GitHub Actions Structure
```yaml
name: CI
on: [push, pull_request]

jobs:
  molecule:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        role:
          - ansible
          - asdf
          - bash
          # ... etc
    steps:
      - uses: actions/checkout@v3
      - name: Run molecule
        run: |
          cd roles/${{ matrix.role }}
          molecule test
```

## Success Criteria

- [ ] Can run `ansible-playbook site.yml --tags shell` to configure shells
- [ ] GitHub Actions runs all molecule tests on every PR
- [ ] External variables from infra repo work seamlessly
- [ ] No complex shared infrastructure to maintain
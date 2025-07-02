# Ansible Collection Dotfiles - Improvements TODO

This document outlines practical improvements for the `marcus_grant.dotfiles` ansible collection, following conventional Ansible collection patterns.

## Repository Rules & Development Process

### Code Quality Standards
- **All code must pass `ansible-lint` and `yamllint`** - No exceptions
- **Follow Ansible best practices** - Use FQCN, proper variable naming, etc.
- **Keep it simple** - Avoid over-engineering solutions

### Python Virtual Environment Requirements
**MANDATORY**: Always use virtual environments for Python projects:

- **NEVER install packages globally** without explicit permission
- **ALWAYS create a venv** before installing project dependencies
- **ALWAYS activate venv** before running any Python/Ansible commands
- Commands must be prefixed with `source venv/bin/activate &&`

### Test-Driven Development (TDD) Process
We follow strict TDD practices for all development:

1. **Red Phase** - Write the test first
   - Write a test in `molecule/default/verify.yml` for a specific behavior
   - The test should fail because the implementation doesn't exist
   - Run `ansible-lint .` to ensure test code passes linting
   - Run `molecule verify` to confirm the test fails

2. **Green Phase** - Make it pass
   - Implement the simplest solution that makes the test pass
   - No extra features, just make the test green
   - Run `ansible-lint .` to ensure implementation passes linting
   - Run `molecule converge` then `molecule verify` to confirm

3. **Refactor Phase** - Clean it up
   - Consider if the implementation can be improved
   - Reconsider if the spec itself needs adjustment
   - Run `ansible-lint .` after any changes
   - Run `molecule test` to ensure everything still works

4. **Repeat** - Next feature
   - Move to the next spec/feature
   - One behavior at a time

**CRITICAL**: 
- ansible-lint must pass at every phase
- All Python commands must run in activated venv

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

### Create Node.js Roles with TDD Workflow
- [x] **[HI]** nodejs_system role - System-level Node.js installation ✅
  - [x] Install nodejs and npm via system package manager
  - [x] Support for installing npm packages globally via npm
  - [x] Support for installing distro-specific Node.js packages
  - [x] Full TDD implementation with comprehensive tests
  - [x] Cross-platform support (Debian, RedHat, other families)
  - [x] Complete documentation and collection integration
- [ ] **[HI]** nvm role - NVM-based Node.js version management
  - [ ] Git-based NVM installation (not curl|bash)
  - [ ] XDG Base Directory Specification compliance by default
  - [ ] Flexible directory control for all NVM locations:
    - [ ] `nvm_dir` - NVM installation directory
    - [ ] `nvm_cache_dir` - Download cache location  
    - [ ] `nvm_node_prefix` - Node.js versions install location
    - [ ] `nvm_npm_config_prefix` - Global npm packages location
  - [ ] XDG compliance options:
    - [ ] `nvm_xdg_compliant: true/false` - Auto-detect XDG vars
    - [ ] Explicit directory overrides when needed
    - [ ] Sensible fallbacks when XDG vars not set
  - [ ] Node.js version management features:
    - [ ] Install specific Node.js versions via `nvm_node_versions: []`
    - [ ] Set default Node.js version via `nvm_default_version`
    - [ ] Shell integration (bash/zsh completion)
  - [ ] Independent role (no dependency on nodejs_system)
  - [ ] Full TDD implementation with molecule tests
  - [ ] Comprehensive documentation

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

### Performance Optimization
- [ ] **[LO]** Optimize molecule container build performance
  - [ ] Investigate Docker layer caching for custom Dockerfiles
  - [ ] Consider pre-built base images for common test scenarios
  - [ ] Evaluate if container build time improves after initial builds

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
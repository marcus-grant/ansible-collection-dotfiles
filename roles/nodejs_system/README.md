# nodejs_system

A system-level Node.js installation and management role for Ansible.
This role installs Node.js and npm via
the distribution package manager and
optionally installs additional Node.js-related packages and global npm packages.

## Requirements

- Ansible Core 2.15+
- Target systems: Debian/Ubuntu, RedHat/Fedora/CentOS
- `community.general` collection (for npm module)

## Role Variables

### Required Variables

None. The role will install Node.js and npm with default settings if
no variables are provided.

### Optional Variables

```yaml
# List of npm packages to install globally via npm
nodejs_system_npm_global_packages: []
# Example:
# nodejs_system_npm_global_packages:
#   - typescript
#   - eslint
#   - @vue/cli

# List of distro packages to install via package manager
nodejs_system_distro_packages: []
# Example for Debian/Ubuntu:
# nodejs_system_distro_packages:
#   - node-gyp
#   - nodejs-doc
# Example for RedHat/Fedora:
# nodejs_system_distro_packages:
#   - nodejs-docs
```

## Dependencies

- `community.general` collection (automatically handles npm installations)

## Supported Platforms

- **Debian/Ubuntu**: Installs `nodejs` and `npm` packages
- **RedHat/Fedora/CentOS**: Installs `nodejs` and `npm` packages  
- **Other distributions**:
  - Basic nodejs/npm installation (distro packages may not work)

## Example Playbooks

### Basic Installation

```yaml
- hosts: servers
  become: true
  roles:
    - marcus_grant.dotfiles.nodejs_system
```

### With Global npm Packages

```yaml
- hosts: development
  become: true
  roles:
    - role: marcus_grant.dotfiles.nodejs_system
      vars:
        nodejs_system_npm_global_packages:
          - typescript
          - eslint
          - nodemon
```

### With Distribution Packages

```yaml
- hosts: build_servers
  become: true
  roles:
    - role: marcus_grant.dotfiles.nodejs_system
      vars:
        nodejs_system_distro_packages:
          - node-gyp
          - nodejs-doc
        nodejs_system_npm_global_packages:
          - typescript
```

### Full Configuration

```yaml
- hosts: all
  become: true
  roles:
    - role: marcus_grant.dotfiles.nodejs_system
      vars:
        nodejs_system_npm_global_packages:
          - typescript
          - eslint
          - prettier
          - nodemon
        nodejs_system_distro_packages: "{{ 
          ['node-gyp', 'nodejs-doc'] if ansible_os_family == 'Debian' 
          else ['nodejs-docs'] if ansible_os_family == 'RedHat'
          else [] }}"
```

## What This Role Does

1. **Updates package cache** on the target system
2. **Installs Node.js and npm** via the distribution package manager
3. **Installs global npm packages** (if specified)
4. **Installs additional distribution packages** (if specified)

## Testing

This role includes comprehensive molecule tests covering:

- Node.js and npm installation verification
- Global npm package installation
- Distribution package installation per OS family
- Multi-platform testing (Debian 12, Debian sid, Fedora)

Run tests with:

```bash
cd roles/nodejs_system
molecule test
```

## License

GPL-3.0-only

## Author Information

Marcus Grant - Part of the marcus_grant.dotfiles collection for
system configuration management.


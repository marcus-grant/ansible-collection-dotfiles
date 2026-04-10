# marcus_grant.dotfiles.userdirs

Ansible role to manage user directories,
either explicitly or via XDG environment variables.

## Requirements

None

## Role Variables

Below is a table of variables,
some optional usually with default values or necessary for the role to function.

| Variable                      | Default        | Choices    | Comments                                      |
| ----------------------------- | -------------- | -----------| --------------------------------------------- |
| userdirs_owner                | *required*     | str        | User whose directories are managed            |
| userdirs_xdg_profile_d        | true           | bool       | Create `XDG_` envars. profile.d file          |
| userdirs_profile_d_path       | *              | str(dir)   | Path to directory of profile.d see *          |
| userdirs_xdg_mkdirs           | true           | bool       | Ensure below `XDG_` dirs exist                |
| userdirs_xdg_bin_home         | .local/bin     | str(dir)+  | Custom value for XDG_BIN_HOME                 |
| userdirs_xdg_data_home        | .local/share   | str(dir)+  | Custom value for XDG_DATA_HOME                |
| userdirs_xdg_config_home      | .config        | str(dir)+  | Custom value for XDG_CONFIG_HOME              |
| userdirs_xdg_cache_home       | .cache         | str(dir)+  | Custom value for XDG_CACHE_HOME               |
| userdirs_xdg_state_home       | .local/state   | str(dir)+  | Custom value for XDG_STATE_HOME               |
| userdirs_custom_dirs          | []             | [str(dir)] | List of absolute paths to create extra dirs   |
| userdirs_user_dirs_enabled    | false          | bool       | Template user-dirs.dirs and user-dirs.locale  |
| userdirs_user_dirs            | **             | dict       | XDG user content dir mappings, see **         |
| userdirs_user_dirs_locale     | en_US          | str        | Locale written to user-dirs.locale            |

> **\***: Default of `userdirs_profile_d_path` uses a three-tier fallback:
> 1. `userdirs_profile_d_path` — explicit override, takes precedence
> 2. `profile_d_path` — provided by `marcus_grant.dotfiles.profile`
> 3. Computed fallback: `<home>/{{ userdirs_xdg_config_home }}/profile.d`

> **+**: These variables are relative paths to the owner's home directory.
> In Linux this is usually `/home/<user>`, in macOS it's `/Users/<user>`.

> **\*\***: Default value for `userdirs_user_dirs`:
> ```yaml
> documents: Documents
> pictures: Pictures
> videos: Videos
> music: Music
> download: Downloads
> desktop: Desktop
> templates: Templates
> publicshare: Public
> ```
> Keys map to `XDG_<KEY>_DIR` entries. Values are relative to `$HOME`.
> Only written when `userdirs_user_dirs_enabled: true`.

### Role Variables Explanation

The main thing this role does is define either custom directories to
ensure are created, or create a partial profile file in a `profile.d` directory
that gets sourced by the shell profile file in `~/.profile`.
XDG variables are associated with some important default user directories
and can be overridden to different paths for various purposes.

To create a partial profile.d file named `10-userdirs.sh`
enable `userdirs_xdg_profile_d`.
Then the variables `userdirs_xdg_{bin_home,data_home,config_home,cache_home,state_home}`
define the paths to their correspondingly named XDG variables as exported environment vars.

If `userdirs_xdg_mkdirs` is enabled the role will also ensure those directories exist.

When `userdirs_user_dirs_enabled: true`, the role templates
`{{ userdirs_xdg_config_home }}/user-dirs.dirs` with the mappings from
`userdirs_user_dirs`, and writes `user-dirs.locale` alongside it. This prevents
`xdg-user-dirs-update` from regenerating the file on login.

## Dependencies

**This role has a hard dependency on `marcus_grant.dotfiles.profile`.**

The `profile` role must run first — it creates the `~/.config/profile.d/` directory
and the `~/.profile` that sources it. Without this, `10-userdirs.sh` has nowhere
to be placed and the XDG variables it exports will never reach the shell environment.

When using the `roles:` key in a playbook this is handled automatically via
`meta/main.yml`. When using `ansible.builtin.include_role` in a tasks context,
you must explicitly run `marcus_grant.dotfiles.profile` first.

## Example Playbook

```yaml
- hosts: all
  roles:
    - name: marcus_grant.dotfiles.profile
      vars:
        profile_user: alice
        profile_group: alice
    - name: marcus_grant.dotfiles.userdirs
      vars:
        userdirs_owner: alice
        userdirs_custom_dirs:
          - /home/alice/projects
```

### With custom XDG user content dirs

```yaml
- name: Apply userdirs role
  ansible.builtin.include_role:
    name: marcus_grant.dotfiles.userdirs
  vars:
    userdirs_owner: alice
    userdirs_user_dirs_enabled: true
    userdirs_user_dirs:
      documents: Documents
      pictures: Media/Photos
      videos: Media/Videos
      music: Media/Music
      download: Downloads
      desktop: Desktop
      templates: Templates
      publicshare: Public
```

## License

GPL3

## Author Information

Marcus Grant
[https://marcusgrant.me](https://marcusgrant.me)
[marcusfg@protonmail.com](marcusfg@protonmail.com)
[github:marcus-grant](https://github.com/marcus-grant)

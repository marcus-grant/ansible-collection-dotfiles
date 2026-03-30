# marcus_grant.dotfiles.userdirs

Ansible role to manage user directories,
either explicitly or via XDG environment variables.

## Requirements

None

## Role Variables

Below is a table of variables,
some optional usually with default values or necessary for the role to function.

| Variable                 | Default        | Choices    | Comments                             |
| ------------------------ | -------------- | -----------| ------------------------------------ |
| userdirs_xdg_profile_d   | true           | bool       | Create `XDG_` envars. profile.d file |
| userdirs_profile_d_path  | *              | str(dir)   | Path to directory of profile.d see * |
| userdirs_xdg_mkdirs      | true           | bool       | Ensure below `XDG_` dirs exist       |
| userdirs_xdg_bin_home    | .local/bin     | str(dir)+  | Custom value for XDG_BIN_HOME        |
| userdirs_xdg_data_home   | .local/share   | str(dir)+  | Custom value for XDG_DATA_HOME       |
| userdirs_xdg_config_home | .config        | str(dir)+  | Custom value for XDG_CONFIG_HOME     |
| userdirs_xdg_cache_home  | .cache         | str(dir)+  | Custom value for XDG_CACHE_HOME      |
| userdirs_xdg_state_home  | .local/state   | str(dir)+  | Custom value for XDG_STATE_HOME      |
| userdirs_custom_dirs     | []             | [str(dir)] | List of paths to create extra dirs   |

> **\***: Default of `userdirs_profile_d_path` can be either of these:
> `profile_d_path` a role variable to `marcus_grant.dotfiles.profile`,
> `~/.config/profile.d` this is also the default value to `profile_d_path`.
> If both `userdirs_profile_d_path` & `profile_d_path` are undefined,
> the default to `profile_d_path` of `~/.config/profile.d` gets used.

> **+**: These variables are relative paths to whatever the user home is.
> In linux this is usually `/home/<user>`, in macOS it's `/Users/<user>`.

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
  vars:
    profile_user: "{{ ansible_user_id }}"
    profile_group: "{{ ansible_user_id }}"
  roles:
    - name: marcus_grant.dotfiles.profile
    - name: marcus_grant.dotfiles.userdirs
      vars:
        userdirs_custom_dirs:
          - "{{ ansible_env.HOME }}/projects"
```

## License

GPL3

## Author Information

Marcus Grant
[https://marcusgrant.me](https://marcusgrant.me)
[marcusfg@protonmail.com](marcusfg@protonmail.com)
[github:marcus-grant](https://github.com/marcus-grant)

#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2026, Marcus Grant <marcusfg@protonmail.com>
# GNU General Public License v2.0+ (see COPYING or https://www.gnu.org/licenses/gpl-2.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

DOCUMENTATION = r'''
---
module: dotfiles_git
short_description: Clone a dotfiles git repo and place shim or symlink config files
version_added: "1.2.0"
description:
  - Clones (or re-clones) a git repository containing dotfiles to a destination directory.
  - For each file mapping, either writes a shell shim (a file containing a C(source) line
    pointing into the cloned repo) or creates a symlink at the expected config location.
  - Shims are idempotent - only written when content differs. Symlinks are only updated
    when the target changes.
options:
  repo:
    description: URL of the git repository to clone.
    required: true
    type: str
  dest:
    description: Filesystem path where the repository will be cloned. Tilde is expanded.
    required: true
    type: str
  version:
    description: Git ref (branch, tag, or commit) to check out.
    type: str
    default: HEAD
  force:
    description:
      - When C(true), delete and re-clone C(dest) even if it already contains a git repo.
    type: bool
    default: false
  files:
    description: List of file placement mappings.
    type: list
    elements: dict
    default: []
    suboptions:
      src:
        description: Path to the file inside the cloned repo (relative to C(dest)).
        required: true
        type: str
      dest:
        description: Absolute path where the program expects this config file.
        required: true
        type: str
      method:
        description:
          - C(shim) writes a shell file containing a C(source) line pointing at C(dest/src).
          - C(symlink) creates a symbolic link at C(dest) pointing at C(dest/src).
        type: str
        choices: [shim, symlink]
        default: shim
      mode:
        description: File permissions for shim files (octal string).
        type: str
        default: '0600'
      prepend_lines:
        description:
          - Extra lines written before the C(source) line in a shim file.
          - Useful for sourcing additional files (e.g. C(source $HOME/.profile)).
        type: list
        elements: str
        default: []
notes:
  - C(prepend_lines) and C(mode) only apply to C(method: shim).
  - Use C(method: symlink) for non-shell config files (vim, tmux, etc.) where a shell
    C(source) line would not be interpreted.
  - Requires the C(git) binary to be present on the target host. Ensure it is installed
    before invoking this module (e.g. via C(ansible.builtin.package)).
seealso:
  - module: ansible.builtin.git
  - module: ansible.builtin.template
author:
  - Marcus Grant (@marcus-grant)
'''

EXAMPLES = r'''
- name: Clone zsh dotfiles and place shims
  marcus_grant.dotfiles.dotfiles_git:
    repo: https://github.com/marcus-grant/dots-zsh
    dest: ~/.config/zsh
    files:
      - src: rc.zsh
        dest: ~/.zshrc
      - src: env.zsh
        dest: ~/.zshenv
        prepend_lines:
          - source $HOME/.profile
      - src: profile.zsh
        dest: ~/.zprofile

- name: Clone vim dotfiles and symlink vimrc
  marcus_grant.dotfiles.dotfiles_git:
    repo: https://github.com/marcus-grant/dots-vim
    dest: ~/.config/vim
    files:
      - src: .vimrc
        dest: ~/.vimrc
        method: symlink

- name: Force re-clone and update shims
  marcus_grant.dotfiles.dotfiles_git:
    repo: https://github.com/marcus-grant/dots-zsh
    dest: ~/.config/zsh
    force: true
    files:
      - src: rc.zsh
        dest: ~/.zshrc
'''

RETURN = r'''
changed:
  description: Whether any change was made (clone, file write, or symlink update).
  returned: always
  type: bool
cloned:
  description: Whether a git clone operation was performed.
  returned: always
  type: bool
diff:
  description: Per-file diff entries for files that changed.
  returned: when files changed
  type: list
  elements: dict
  contains:
    path:
      description: Destination file path.
      type: str
    before:
      description: File content or symlink target before the change (empty if new).
      type: str
    after:
      description: File content or symlink target after the change.
      type: str
'''

import os
import shutil
import subprocess
from pathlib import Path

from ansible.module_utils.basic import AnsibleModule


# ---------------------------------------------------------------------------
# Pure helper functions — imported directly by unit tests
# ---------------------------------------------------------------------------

def _ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def generate_shim_content(dest, src, prepend_lines):
    lines = ['# Ansible managed - do not edit']
    lines.extend(prepend_lines)
    lines.append(f'source {Path(dest) / src}')
    return '\n'.join(lines) + '\n'


def place_shim_file(file_dest, content, mode='0600'):
    file_dest = Path(file_dest).expanduser()
    _ensure_parent(file_dest)

    before = file_dest.read_text() if file_dest.exists() else ''

    if before == content:
        return False, None

    file_dest.write_text(content)
    file_dest.chmod(int(mode, 8))

    return True, {'path': str(file_dest), 'before': before, 'after': content}


def place_symlink(link_path, target_path):
    link_path = Path(link_path).expanduser()
    target_path = Path(target_path).expanduser()
    _ensure_parent(link_path)

    if link_path.is_symlink():
        if Path(os.readlink(link_path)) == target_path:
            return False
        link_path.unlink()

    link_path.symlink_to(target_path)
    return True


def git_clone_or_skip(repo, dest, version, force):
    dest = Path(dest).expanduser()
    already_cloned = (dest / '.git').is_dir()

    if already_cloned and not force:
        return False

    if already_cloned:
        shutil.rmtree(dest)

    cmd = ['git', 'clone']
    if version and version != 'HEAD':
        cmd += ['--branch', version]
    cmd += [repo, str(dest)]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(f'git clone failed: {result.stderr}')

    return True


# ---------------------------------------------------------------------------
# Ansible module entry point
# ---------------------------------------------------------------------------

_FILE_SPEC = dict(
    src=dict(type='str', required=True),
    dest=dict(type='str', required=True),
    method=dict(type='str', default='shim', choices=['shim', 'symlink']),
    mode=dict(type='str', default='0600'),
    prepend_lines=dict(type='list', elements='str', default=[]),
)


def run_module():
    module = AnsibleModule(
        argument_spec=dict(
            repo=dict(type='str', required=True),
            dest=dict(type='str', required=True),
            version=dict(type='str', default='HEAD'),
            force=dict(type='bool', default=False),
            files=dict(type='list', elements='dict', default=[], options=_FILE_SPEC),
        ),
        supports_check_mode=False,
    )

    repo = module.params['repo']
    dest = module.params['dest']
    version = module.params['version']
    force = module.params['force']
    files = module.params['files']

    cloned = False
    try:
        cloned = git_clone_or_skip(repo, dest, version, force)
    except RuntimeError as exc:
        module.fail_json(msg=str(exc))

    changed = cloned
    dest_expanded = str(Path(dest).expanduser())
    diffs = []

    for f in files:
        if f['method'] == 'shim':
            content = generate_shim_content(dest_expanded, f['src'], f['prepend_lines'])
            file_changed, diff = place_shim_file(f['dest'], content, f['mode'])
        else:
            target = str(Path(dest_expanded) / f['src'])
            file_changed = place_symlink(f['dest'], target)
            diff = {'path': f['dest'], 'before': '', 'after': target} if file_changed else None

        if file_changed:
            changed = True
        if diff:
            diffs.append(diff)

    module.exit_json(changed=changed, cloned=cloned, diff=diffs)


def main():
    run_module()


if __name__ == '__main__':
    main()

#!/usr/bin/python
# -*- coding: utf-8 -*-

import os
import shutil
import subprocess
from pathlib import Path


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

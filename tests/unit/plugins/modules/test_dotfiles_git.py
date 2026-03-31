# -*- coding: utf-8 -*-
# Tests for the dotfiles_git Ansible module.
# Run with: python -m pytest tests/unit/ -v

import os
import pytest
from unittest.mock import patch, MagicMock

# RED: import fails until plugins/modules/dotfiles_git.py exists
from ansible_collections.marcus_grant.dotfiles.plugins.modules.dotfiles_git import (
    generate_shim_content,
    place_shim_file,
    place_symlink,
    git_clone_or_pull,
    run_module,
)


class TestGenerateShimContent:
    def test_basic_source_line(self):
        content = generate_shim_content('/root/.config/zsh', 'rc.zsh', [])
        assert 'source /root/.config/zsh/rc.zsh' in content

    def test_managed_header_present(self):
        content = generate_shim_content('/root/.config/zsh', 'rc.zsh', [])
        assert '# Ansible managed' in content

    def test_prepend_lines_appear_before_source(self):
        content = generate_shim_content(
            '/root/.config/zsh', 'env.zsh', ['source $HOME/.profile']
        )
        lines = content.strip().splitlines()
        profile_idx = next(i for i, l in enumerate(lines) if '$HOME/.profile' in l)
        source_idx = next(i for i, l in enumerate(lines) if 'env.zsh' in l)
        assert profile_idx < source_idx

    def test_prepend_lines_all_present(self):
        content = generate_shim_content(
            '/root/.config/zsh', 'env.zsh',
            ['source $HOME/.profile', 'export FOO=bar']
        )
        assert 'source $HOME/.profile' in content
        assert 'export FOO=bar' in content

    def test_empty_prepend_lines_no_extra_content(self):
        content = generate_shim_content('/root/.config/zsh', 'rc.zsh', [])
        non_comment_lines = [l for l in content.splitlines() if l and not l.startswith('#')]
        assert len(non_comment_lines) == 1
        assert 'source' in non_comment_lines[0]

    def test_tilde_in_dest_not_expanded(self):
        content = generate_shim_content('~/.config/zsh', 'rc.zsh', [])
        assert 'source ~/.config/zsh/rc.zsh' in content

    def test_content_ends_with_newline(self):
        content = generate_shim_content('/root/.config/zsh', 'rc.zsh', [])
        assert content.endswith('\n')


class TestPlaceShimFile:
    def test_missing_file_is_created(self, tmp_path):
        target = str(tmp_path / 'zshrc')
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        changed, diff = place_shim_file(target, content)
        assert changed is True
        with open(target) as f:
            assert f.read() == content

    def test_matching_content_is_not_changed(self, tmp_path):
        target = tmp_path / 'zshrc'
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        target.write_text(content)
        changed, diff = place_shim_file(str(target), content)
        assert changed is False

    def test_different_content_is_overwritten(self, tmp_path):
        target = tmp_path / 'zshrc'
        target.write_text('old content\n')
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        changed, diff = place_shim_file(str(target), content)
        assert changed is True
        assert target.read_text() == content

    def test_diff_returned_on_change(self, tmp_path):
        target = tmp_path / 'zshrc'
        target.write_text('old content\n')
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        changed, diff = place_shim_file(str(target), content)
        assert diff is not None
        assert diff['before'] == 'old content\n'
        assert diff['after'] == content

    def test_no_diff_when_unchanged(self, tmp_path):
        target = tmp_path / 'zshrc'
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        target.write_text(content)
        changed, diff = place_shim_file(str(target), content)
        assert diff is None

    def test_parent_dirs_created(self, tmp_path):
        target = str(tmp_path / 'subdir' / 'zshrc')
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        changed, diff = place_shim_file(target, content)
        assert changed is True
        assert os.path.isfile(target)

    def test_file_mode_is_set(self, tmp_path):
        target = tmp_path / 'zshrc'
        content = '# Ansible managed\nsource /root/.config/zsh/rc.zsh\n'
        place_shim_file(str(target), content, mode='0600')
        mode = oct(os.stat(str(target)).st_mode)[-4:]
        assert mode == '0600'


class TestPlaceSymlink:
    @pytest.fixture
    def src(self, tmp_path):
        f = tmp_path / 'rc.zsh'
        f.write_text('# zsh\n')
        return f

    def test_missing_symlink_is_created(self, tmp_path, src):
        link = str(tmp_path / '.zshrc')
        changed = place_symlink(link, str(src))
        assert changed is True
        assert os.path.islink(link)
        assert os.readlink(link) == str(src)

    def test_correct_symlink_is_not_changed(self, tmp_path, src):
        link = tmp_path / '.zshrc'
        os.symlink(str(src), str(link))
        changed = place_symlink(str(link), str(src))
        assert changed is False

    def test_wrong_target_is_updated(self, tmp_path, src):
        other = tmp_path / 'other.zsh'
        other.write_text('# other\n')
        link = tmp_path / '.zshrc'
        os.symlink(str(other), str(link))
        changed = place_symlink(str(link), str(src))
        assert changed is True
        assert os.readlink(str(link)) == str(src)

    def test_parent_dirs_created(self, tmp_path, src):
        link = str(tmp_path / 'nested' / 'dir' / '.zshrc')
        changed = place_symlink(link, str(src))
        assert changed is True
        assert os.path.islink(link)


class TestGitCloneOrPull:
    REPO = 'https://github.com/example/dots-zsh'

    @pytest.fixture
    def ok_run(self):
        return MagicMock(returncode=0, stdout='', stderr='')

    @pytest.fixture
    def fail_run(self):
        return MagicMock(returncode=1, stdout='', stderr='fatal: repo not found')

    @pytest.fixture
    def pull_changed_run(self):
        return MagicMock(returncode=0, stdout='Updating abc123..def456\n', stderr='')

    @pytest.fixture
    def pull_noop_run(self):
        return MagicMock(returncode=0, stdout='Already up to date.\n', stderr='')

    def test_no_git_dir_triggers_clone(self, tmp_path, ok_run):
        dest = str(tmp_path / 'zsh')
        with patch('subprocess.run', return_value=ok_run) as mock_run:
            result = git_clone_or_pull(self.REPO, dest, 'HEAD', False, False)
        assert result is True
        assert 'clone' in mock_run.call_args[0][0]

    def test_existing_git_dir_update_false_skips(self, tmp_path):
        dest = tmp_path / 'zsh'
        (dest / '.git').mkdir(parents=True)
        with patch('subprocess.run') as mock_run:
            result = git_clone_or_pull(self.REPO, str(dest), 'HEAD', False, False)
        assert result is False
        mock_run.assert_not_called()

    def test_existing_git_dir_update_true_pulls(self, tmp_path, pull_changed_run):
        dest = tmp_path / 'zsh'
        (dest / '.git').mkdir(parents=True)
        with patch('subprocess.run', return_value=pull_changed_run) as mock_run:
            result = git_clone_or_pull(self.REPO, str(dest), 'HEAD', False, True)
        assert result is True
        assert 'pull' in mock_run.call_args[0][0]

    def test_pull_already_up_to_date_returns_false(self, tmp_path, pull_noop_run):
        dest = tmp_path / 'zsh'
        (dest / '.git').mkdir(parents=True)
        with patch('subprocess.run', return_value=pull_noop_run):
            result = git_clone_or_pull(self.REPO, str(dest), 'HEAD', False, True)
        assert result is False

    def test_force_reclones_existing(self, tmp_path, ok_run):
        dest = tmp_path / 'zsh'
        (dest / '.git').mkdir(parents=True)
        with patch('subprocess.run', return_value=ok_run), \
             patch('shutil.rmtree') as mock_rm:
            result = git_clone_or_pull(self.REPO, str(dest), 'HEAD', True, False)
        assert result is True
        mock_rm.assert_called_once_with(dest)

    def test_force_on_missing_dest_skips_rmtree(self, tmp_path, ok_run):
        dest = str(tmp_path / 'zsh')
        with patch('subprocess.run', return_value=ok_run), \
             patch('shutil.rmtree') as mock_rm:
            result = git_clone_or_pull(self.REPO, dest, 'HEAD', True, False)
        assert result is True
        mock_rm.assert_not_called()

    def test_clone_failure_raises(self, tmp_path, fail_run):
        dest = str(tmp_path / 'zsh')
        with patch('subprocess.run', return_value=fail_run):
            with pytest.raises(RuntimeError):
                git_clone_or_pull(self.REPO, dest, 'HEAD', False, False)

    def test_pull_failure_raises(self, tmp_path, fail_run):
        dest = tmp_path / 'zsh'
        (dest / '.git').mkdir(parents=True)
        with patch('subprocess.run', return_value=fail_run):
            with pytest.raises(RuntimeError):
                git_clone_or_pull(self.REPO, str(dest), 'HEAD', False, True)


class TestRunModule:
    REPO = 'https://github.com/marcus-grant/dots-zsh'

    @pytest.fixture
    def module(self):
        m = MagicMock()
        m.params = {
            'repo': self.REPO,
            'dest': '/root/.config/zsh',
            'version': 'HEAD',
            'force': False,
            'update': False,
            'files': [],
        }
        return m

    @pytest.fixture
    def ansible_module_mock(self, module):
        with patch(
            'ansible_collections.marcus_grant.dotfiles.plugins.modules'
            '.dotfiles_git.AnsibleModule',
            return_value=module,
        ):
            yield module

    def test_calls_git_clone_or_pull(self, ansible_module_mock):
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False) as mock_git:
            run_module()
        mock_git.assert_called_once_with(self.REPO, '/root/.config/zsh', 'HEAD', False, False)

    def test_changed_true_when_cloned(self, ansible_module_mock):
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=True):
            run_module()
        ansible_module_mock.exit_json.assert_called_once()
        assert ansible_module_mock.exit_json.call_args[1]['changed'] is True

    def test_changed_false_when_nothing_changed(self, ansible_module_mock):
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False):
            run_module()
        assert ansible_module_mock.exit_json.call_args[1]['changed'] is False

    def test_shim_file_placed_for_shim_method(self, ansible_module_mock):
        ansible_module_mock.params['files'] = [{
            'src': 'rc.zsh', 'dest': '/root/.zshrc',
            'method': 'shim', 'mode': '0600', 'prepend_lines': [],
        }]
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False), \
             patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.place_shim_file', return_value=(False, None)) as mock_shim:
            run_module()
        mock_shim.assert_called_once()

    def test_symlink_placed_for_symlink_method(self, ansible_module_mock):
        ansible_module_mock.params['files'] = [{
            'src': 'rc.zsh', 'dest': '/root/.zshrc_sym',
            'method': 'symlink', 'mode': '0600', 'prepend_lines': [],
        }]
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False), \
             patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.place_symlink', return_value=False) as mock_link:
            run_module()
        mock_link.assert_called_once()

    def test_fail_json_called_on_clone_error(self, ansible_module_mock):
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull',
                   side_effect=RuntimeError('git clone failed: fatal')):
            run_module()
        ansible_module_mock.fail_json.assert_called_once()

    def test_changed_true_when_file_changed(self, ansible_module_mock):
        ansible_module_mock.params['files'] = [{
            'src': 'rc.zsh', 'dest': '/root/.zshrc',
            'method': 'shim', 'mode': '0600', 'prepend_lines': [],
        }]
        diff = {'path': '/root/.zshrc', 'before': '', 'after': 'source ...'}
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False), \
             patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.place_shim_file', return_value=(True, diff)):
            run_module()
        assert ansible_module_mock.exit_json.call_args[1]['changed'] is True

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
    _extract_ssh_hostname,
    check_ssh_preflight,
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

    def test_ssh_preflight_failure_calls_fail_json(self, ansible_module_mock):
        ansible_module_mock.params['repo'] = 'git@github.com:user/dots.git'
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.check_ssh_preflight',
                   return_value='SSH not configured for github.com — ensure ssh_config role has run.'), \
             patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False) as mock_clone:
            run_module()
        ansible_module_mock.fail_json.assert_called_once()
        mock_clone.assert_not_called()

    def test_ssh_preflight_success_proceeds_to_clone(self, ansible_module_mock):
        ansible_module_mock.params['repo'] = 'git@github.com:user/dots.git'
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.check_ssh_preflight', return_value=None), \
             patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False) as mock_clone:
            run_module()
        mock_clone.assert_called_once()
        ansible_module_mock.fail_json.assert_not_called()

    def test_ssh_preflight_error_message_passed_to_fail_json(self, ansible_module_mock):
        msg = 'SSH not configured for github.com — ensure ssh_config role has run.'
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.check_ssh_preflight', return_value=msg):
            run_module()
        ansible_module_mock.fail_json.assert_called_once_with(msg=msg)

    def test_https_url_does_not_trigger_fail_json(self, ansible_module_mock):
        with patch('ansible_collections.marcus_grant.dotfiles.plugins.modules'
                   '.dotfiles_git.git_clone_or_pull', return_value=False):
            run_module()
        ansible_module_mock.fail_json.assert_not_called()


class TestExtractSshHostname:
    def test_git_at_url_returns_hostname(self):
        assert _extract_ssh_hostname('git@github.com:user/repo.git') == 'github.com'

    def test_ssh_scheme_url_returns_hostname(self):
        assert _extract_ssh_hostname('ssh://git@github.com/user/repo.git') == 'github.com'

    def test_https_url_returns_none(self):
        assert _extract_ssh_hostname('https://github.com/user/repo.git') is None

    def test_file_url_returns_none(self):
        assert _extract_ssh_hostname('file:///home/user/repo.git') is None

    def test_plain_path_returns_none(self):
        assert _extract_ssh_hostname('/home/user/repo.git') is None

    def test_ssh_scheme_with_port_strips_port(self):
        assert _extract_ssh_hostname('ssh://git@github.com:2222/user/repo.git') == 'github.com'

    def test_git_at_subdomain_preserved(self):
        assert _extract_ssh_hostname('git@gitlab.company.internal:team/repo.git') == 'gitlab.company.internal'

    def test_ssh_scheme_no_user_returns_hostname(self):
        assert _extract_ssh_hostname('ssh://github.com/user/repo.git') == 'github.com'

    def test_empty_string_returns_none(self):
        assert _extract_ssh_hostname('') is None


class TestCheckSshPreflight:
    REPO = 'git@github.com:user/dots.git'
    HOST = 'github.com'

    def _make_known_hosts(self, home, hostname=None):
        ssh_dir = home / '.ssh'
        ssh_dir.mkdir(parents=True, exist_ok=True)
        kh = ssh_dir / 'known_hosts'
        if hostname:
            kh.write_text(f'{hostname} ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAA\n')
        else:
            kh.write_text('')
        return kh

    def test_non_ssh_url_returns_none(self, tmp_path):
        assert check_ssh_preflight('https://github.com/u/r.git', str(tmp_path)) is None

    def test_known_hosts_missing_returns_error(self, tmp_path):
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None
        assert 'known_hosts' in err

    def test_known_hosts_empty_returns_error(self, tmp_path):
        self._make_known_hosts(tmp_path)  # empty
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None
        assert self.HOST in err

    def test_known_hosts_hostname_absent_returns_error(self, tmp_path):
        self._make_known_hosts(tmp_path, 'notgithub.com')
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None
        assert self.HOST in err

    def test_known_hosts_hostname_as_suffix_substring_returns_error(self, tmp_path):
        # 'notgithub.com' contains 'github.com' as suffix — must not match
        self._make_known_hosts(tmp_path, 'notgithub.com')
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None

    def test_known_hosts_hostname_as_prefix_substring_returns_error(self, tmp_path):
        # 'github.com.evil.org' contains 'github.com' as prefix — must not match
        self._make_known_hosts(tmp_path, 'github.com.evil.org')
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None

    def test_managed_conf_present_returns_none(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        conf_d = tmp_path / '.ssh' / 'config.d'
        conf_d.mkdir(parents=True, exist_ok=True)
        (conf_d / f'managed-{self.HOST}.conf').write_text('Host github.com\n')
        assert check_ssh_preflight(self.REPO, str(tmp_path)) is None

    def test_ssh_config_contains_hostname_returns_none(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        (tmp_path / '.ssh' / 'config').write_text(f'Host {self.HOST}\n  User git\n')
        assert check_ssh_preflight(self.REPO, str(tmp_path)) is None

    def test_no_config_d_and_no_ssh_config_returns_error(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None
        assert self.HOST in err

    def test_config_d_dir_exists_but_wrong_file_returns_error(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        conf_d = tmp_path / '.ssh' / 'config.d'
        conf_d.mkdir(parents=True, exist_ok=True)
        (conf_d / 'managed-other.com.conf').write_text('Host other.com\n')
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None

    def test_ssh_config_exists_but_hostname_absent_returns_error(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        (tmp_path / '.ssh' / 'config').write_text('Host other.com\n  User git\n')
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert err is not None

    def test_error_message_contains_role_hint(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert 'ssh_config' in err

    def test_managed_conf_priority_over_missing_ssh_config(self, tmp_path):
        self._make_known_hosts(tmp_path, self.HOST)
        conf_d = tmp_path / '.ssh' / 'config.d'
        conf_d.mkdir(parents=True, exist_ok=True)
        (conf_d / f'managed-{self.HOST}.conf').write_text('Host github.com\n')
        # No ~/.ssh/config at all
        assert check_ssh_preflight(self.REPO, str(tmp_path)) is None

    def test_no_config_d_dir_no_exception(self, tmp_path):
        # config.d directory does not exist — must not raise
        self._make_known_hosts(tmp_path, self.HOST)
        err = check_ssh_preflight(self.REPO, str(tmp_path))
        assert isinstance(err, str)  # returns error, not raises

    def test_home_dir_not_exists_returns_error(self, tmp_path):
        nonexistent = str(tmp_path / 'ghost')
        err = check_ssh_preflight(self.REPO, nonexistent)
        assert err is not None
        assert 'known_hosts' in err

    def test_port_in_ssh_url_hostname_stripped(self, tmp_path):
        repo = 'ssh://git@github.com:2222/user/dots.git'
        self._make_known_hosts(tmp_path, self.HOST)
        (tmp_path / '.ssh' / 'config.d').mkdir(parents=True, exist_ok=True)
        (tmp_path / '.ssh' / 'config.d' / f'managed-{self.HOST}.conf').write_text('')
        assert check_ssh_preflight(repo, str(tmp_path)) is None

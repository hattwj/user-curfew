from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest


SCRIPT = os.path.realpath("/usr/local/bin/user-curfew")
CONFIG = os.path.realpath("/etc/user-curfew.toml")
CRON_LINE = "*/5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"


class TestInstallCron:
    def test_new_install_empty_crontab(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 1

        proc_install = MagicMock()
        proc_install.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_install]) as mock_run:
            module.install_cron(SCRIPT, CONFIG, 5)

        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "crontab entry installed" in captured.out

    def test_new_install_existing_crontab_no_duplicate(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "0 3 * * * /usr/bin/some-other-job\n"

        proc_install = MagicMock()
        proc_install.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_install]) as mock_run:
            module.install_cron(SCRIPT, CONFIG, 5)

        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "crontab entry installed" in captured.out

    def test_duplicate_entry_no_changes(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = CRON_LINE

        with patch("subprocess.run", return_value=proc_list) as mock_run:
            module.install_cron(SCRIPT, CONFIG, 5)

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "no changes needed" in captured.out

    def test_update_existing_entry_different_interval(self, module, capsys):
        old_line = "*/10 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = old_line

        proc_update = MagicMock()
        proc_update.returncode = 0

        with patch("subprocess.run",
                   side_effect=[proc_list, proc_update]) as mock_run:
            module.install_cron(SCRIPT, CONFIG, 5)

        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "updating to:" in captured.out
        assert "crontab updated" in captured.out

    def test_skips_commented_entries(self, module, capsys):
        commented_line = "# */5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
        other_line = "0 2 * * * /usr/bin/backup\n"
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = commented_line + other_line

        proc_install = MagicMock()
        proc_install.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_install]) as mock_run:
            module.install_cron(SCRIPT, CONFIG, 5)

        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "crontab entry installed" in captured.out

    def test_install_failure(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 1

        proc_install = MagicMock()
        proc_install.returncode = 1
        proc_install.stderr = "permission denied"

        with patch("subprocess.run",
                   side_effect=[proc_list, proc_install]):
            with pytest.raises(SystemExit):
                module.install_cron(SCRIPT, CONFIG, 5)

    def test_update_failure(self, module):
        old_line = "*/10 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = old_line

        proc_update = MagicMock()
        proc_update.returncode = 1
        proc_update.stderr = "permission denied"

        with patch("subprocess.run",
                   side_effect=[proc_list, proc_update]):
            with pytest.raises(SystemExit):
                module.install_cron(SCRIPT, CONFIG, 5)

    def test_crontab_no_newline_at_end_still_works(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "0 3 * * * /usr/bin/backup"

        proc_install = MagicMock()
        proc_install.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_install]):
            module.install_cron(SCRIPT, CONFIG, 5)

        captured = capsys.readouterr()
        assert "crontab entry installed" in captured.out

    def test_interval_shown_in_output(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 1
        proc_install = MagicMock()
        proc_install.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_install]):
            module.install_cron(SCRIPT, CONFIG, 10)

        captured = capsys.readouterr()
        assert "every 10 minute" in captured.out


class TestUninstallCron:
    def test_removes_matching_entry(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = (
            "0 3 * * * /usr/bin/backup\n"
            "*/5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
        )

        proc_uninstall = MagicMock()
        proc_uninstall.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_uninstall]) as mock_run:
            module.uninstall_cron(SCRIPT)

        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "removed 1 crontab entry" in captured.out

    def test_removes_multiple_entries(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = (
            "*/5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
            "*/10 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/other.toml\n"
        )

        proc_uninstall = MagicMock()
        proc_uninstall.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_uninstall]) as mock_run:
            module.uninstall_cron(SCRIPT)

        assert mock_run.call_count == 2
        captured = capsys.readouterr()
        assert "removed 2 crontab entry" in captured.out

    def test_no_matching_entry(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "0 3 * * * /usr/bin/backup\n"

        with patch("subprocess.run", return_value=proc_list) as mock_run:
            module.uninstall_cron(SCRIPT)

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "no matching crontab entry found" in captured.out

    def test_no_crontab_at_all(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 1

        with patch("subprocess.run", return_value=proc_list) as mock_run:
            module.uninstall_cron(SCRIPT)

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "no crontab entries found" in captured.out

    def test_skips_commented_entries(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = (
            "0 3 * * * /usr/bin/backup\n"
            "# */5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
        )

        with patch("subprocess.run", return_value=proc_list) as mock_run:
            module.uninstall_cron(SCRIPT)

        mock_run.assert_called_once()
        captured = capsys.readouterr()
        assert "no matching crontab entry found" in captured.out

    def test_preserves_other_entries(self, module, capsys):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = (
            "0 3 * * * /usr/bin/backup\n"
            "*/5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
            "0 5 * * * /usr/bin/cleanup\n"
        )

        proc_uninstall = MagicMock()
        proc_uninstall.returncode = 0

        with patch("subprocess.run", side_effect=[proc_list, proc_uninstall]) as mock_run:
            module.uninstall_cron(SCRIPT)

        assert mock_run.call_count == 2
        new_crontab = mock_run.call_args_list[1].kwargs["input"]
        assert "0 3 * * * /usr/bin/backup" in new_crontab
        assert "0 5 * * * /usr/bin/cleanup" in new_crontab
        assert SCRIPT not in new_crontab

    def test_uninstall_failure(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = (
            "*/5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
        )

        proc_uninstall = MagicMock()
        proc_uninstall.returncode = 1
        proc_uninstall.stderr = "permission denied"

        with patch("subprocess.run", side_effect=[proc_list, proc_uninstall]):
            with pytest.raises(SystemExit):
                module.uninstall_cron(SCRIPT)


class TestDefaultConfigPath:
    def test_default_config_path(self, module):
        path = module.default_config_path()
        assert path.name == "user-curfew.toml"

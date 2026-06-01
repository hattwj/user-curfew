from __future__ import annotations

import subprocess
from unittest.mock import MagicMock, patch

import pytest


class TestRun:
    def test_normal_mode(self, module):
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = MagicMock()
            result = module.run(["echo", "hello"], dry_run=False)
            mock_run.assert_called_once_with(
                ["echo", "hello"], capture_output=True, text=True
            )
            assert result is mock_run.return_value

    def test_dry_run_mode(self, module):
        with patch("subprocess.run") as mock_run, \
             patch.object(module.log, "info") as mock_log:
            result = module.run(["echo", "hello"], dry_run=True)
            mock_run.assert_not_called()
            assert result is None
            mock_log.assert_called_once()
            assert "[dry-run] would run:" in mock_log.call_args[0][0]


class TestIsAccountLocked:
    def test_locked_account(self, module):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = "testuser L 2025-01-01 0 99999 7 -1"
        with patch("subprocess.run", return_value=proc):
            assert module.is_account_locked("testuser") is True

    def test_unlocked_account_password(self, module):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = "testuser P 2025-01-01 0 99999 7 -1"
        with patch("subprocess.run", return_value=proc):
            assert module.is_account_locked("testuser") is False

    def test_unlocked_account_no_password(self, module):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = "testuser NP 2025-01-01 0 99999 7 -1"
        with patch("subprocess.run", return_value=proc):
            assert module.is_account_locked("testuser") is False

    def test_passwd_command_fails(self, module):
        proc = MagicMock()
        proc.returncode = 1
        proc.stderr = "Error"
        with patch("subprocess.run", return_value=proc):
            assert module.is_account_locked("testuser") is False

    def test_unexpected_output_format(self, module):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = ""
        with patch("subprocess.run", return_value=proc):
            assert module.is_account_locked("testuser") is False

    def test_single_field_output(self, module):
        proc = MagicMock()
        proc.returncode = 0
        proc.stdout = "testuser"
        with patch("subprocess.run", return_value=proc):
            assert module.is_account_locked("testuser") is False


class TestUserExists:
    def test_user_exists(self, module):
        proc = MagicMock()
        proc.returncode = 0
        with patch("subprocess.run", return_value=proc):
            assert module.user_exists("testuser") is True

    def test_user_does_not_exist(self, module):
        proc = MagicMock()
        proc.returncode = 1
        with patch("subprocess.run", return_value=proc):
            assert module.user_exists("testuser") is False


class TestLockAccount:
    def test_lock_with_kill(self, module):
        with patch.object(module, "run") as mock_run, patch.object(
            module, "terminate_sessions"
        ) as mock_terminate:
            module.lock_account("testuser", kill=True, dry_run=False)
            mock_run.assert_called_once_with(
                ["passwd", "--lock", "testuser"], False
            )
            mock_terminate.assert_called_once_with("testuser", False)

    def test_lock_without_kill(self, module):
        with patch.object(module, "run") as mock_run, patch.object(
            module, "terminate_sessions"
        ) as mock_terminate:
            module.lock_account("testuser", kill=False, dry_run=False)
            mock_run.assert_called_once_with(
                ["passwd", "--lock", "testuser"], False
            )
            mock_terminate.assert_not_called()

    def test_lock_dry_run(self, module):
        with patch.object(module, "run") as mock_run, patch.object(
            module, "terminate_sessions"
        ) as mock_terminate:
            module.lock_account("testuser", kill=True, dry_run=True)
            mock_run.assert_called_once_with(
                ["passwd", "--lock", "testuser"], True
            )
            mock_terminate.assert_called_once_with("testuser", True)


class TestUnlockAccount:
    def test_unlock(self, module):
        with patch.object(module, "run") as mock_run:
            module.unlock_account("testuser", dry_run=False)
            mock_run.assert_called_once_with(
                ["passwd", "--unlock", "testuser"], False
            )

    def test_unlock_dry_run(self, module):
        with patch.object(module, "run") as mock_run:
            module.unlock_account("testuser", dry_run=True)
            mock_run.assert_called_once_with(
                ["passwd", "--unlock", "testuser"], True
            )


class TestTerminateSessions:
    def test_user_has_sessions_loginctl_success(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "c1   1000   testuser   seat0   tty1\n"

        proc_term = MagicMock()
        proc_term.returncode = 0

        side_effects = [proc_list, proc_term]

        with patch("subprocess.run", side_effect=side_effects) as mock_run:
            module.terminate_sessions("testuser", dry_run=False)

        assert mock_run.call_count == 2
        assert mock_run.call_args_list[0].args[0] == [
            "loginctl", "list-sessions", "--no-legend"
        ]
        assert mock_run.call_args_list[1].args[0] == [
            "loginctl", "terminate-user", "testuser"
        ]

    def test_user_has_no_sessions(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "c1   1000   someone_else   seat0   tty1\n"

        with patch("subprocess.run", return_value=proc_list) as mock_run:
            module.terminate_sessions("testuser", dry_run=False)

        mock_run.assert_called_once()
        assert mock_run.call_args.args[0] == [
            "loginctl", "list-sessions", "--no-legend"
        ]

    def test_loginctl_list_fails_pkill_fallback(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 1

        side_effects = [proc_list, MagicMock()]

        with patch("subprocess.run", side_effect=side_effects) as mock_run:
            module.terminate_sessions("testuser", dry_run=False)

        assert mock_run.call_count == 2
        assert mock_run.call_args_list[1].args[0] == [
            "pkill", "-KILL", "-u", "testuser"
        ]

    def test_terminate_user_fails_pkill_fallback(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "c1   1000   testuser   seat0   tty1\n"

        proc_term = MagicMock()
        proc_term.returncode = 1
        proc_term.stderr = "some error"

        proc_pkill = MagicMock()

        side_effects = [proc_list, proc_term, proc_pkill]

        with patch("subprocess.run", side_effect=side_effects) as mock_run:
            module.terminate_sessions("testuser", dry_run=False)

        assert mock_run.call_count == 3
        assert mock_run.call_args_list[2].args[0] == [
            "pkill", "-KILL", "-u", "testuser"
        ]

    def test_dry_run_does_not_execute_commands(self, module):
        proc_list = MagicMock()
        proc_list.returncode = 0
        proc_list.stdout = "c1   1000   testuser   seat0   tty1\n"

        proc_pkill = MagicMock()

        with patch("subprocess.run", side_effect=[proc_list, proc_pkill]) as mock_subprocess, \
             patch.object(module, "run") as mock_run:
            module.terminate_sessions("testuser", dry_run=True)

        mock_subprocess.assert_called_once()
        assert mock_run.call_count == 2
        all_dry = all(call.args[1] is True for call in mock_run.call_args_list)
        assert all_dry

    def test_loginctl_output_with_multiple_users(self, module):
        proc_list = subprocess.CompletedProcess(
            args=[], returncode=0,
            stdout=(
                "c1   1000   alice   seat0   tty1\n"
                "c2   1001   bob     seat1   tty2\n"
                "c3   1002   testuser seat2  tty3\n"
            ),
        )

        proc_term = subprocess.CompletedProcess(args=[], returncode=0)

        side_effects = [proc_list, proc_term]

        with patch("subprocess.run", side_effect=side_effects) as mock_run:
            module.terminate_sessions("testuser", dry_run=False)

        assert mock_run.call_count == 2
        assert mock_run.call_args_list[1].args[0] == [
            "loginctl", "terminate-user", "testuser"
        ]


class TestSendNotification:
    def test_send_notification(self, module):
        with patch.object(module, "run") as mock_run:
            module.send_notification("testuser", 10, dry_run=False)

        mock_run.assert_called_once()
        cmd = mock_run.call_args[0][0]
        assert cmd[0] == "systemd-run"
        assert cmd[1] == "--machine=testuser@.host"
        assert cmd[2] == "--user"
        assert cmd[3] == "notify-send"
        assert cmd[4] == "Account Curfew"
        assert "10" in cmd[5]

    def test_send_notification_dry_run(self, module):
        with patch.object(module, "run") as mock_run:
            module.send_notification("testuser", 3, dry_run=True)

        mock_run.assert_called_once()
        assert mock_run.call_args[0][1] is True


class TestMinutesUntilLock:
    def test_lock_in_future(self, module):
        import datetime
        now = datetime.datetime(2025, 6, 2, 22, 50, 0)
        lock_time = datetime.time(23, 0)
        assert module._minutes_until_lock(now, lock_time) == 10

    def test_lock_same_time(self, module):
        import datetime
        now = datetime.datetime(2025, 6, 2, 23, 0, 0)
        lock_time = datetime.time(23, 0)
        assert module._minutes_until_lock(now, lock_time) == 0

    def test_lock_just_passed(self, module):
        import datetime
        now = datetime.datetime(2025, 6, 2, 23, 1, 0)
        lock_time = datetime.time(23, 0)
        assert module._minutes_until_lock(now, lock_time) == -1

from __future__ import annotations

import datetime
from unittest.mock import MagicMock, patch

from freezegun import freeze_time


def test_show_status_with_users(module, sample_entries, notif_disabled, capsys):
    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", side_effect=[True, False]):
            module.show_status(sample_entries, notif_disabled)

    captured = capsys.readouterr()
    assert "Current time:" in captured.out
    assert "alice:" in captured.out
    assert "bob:" in captured.out
    assert "LOCKED" in captured.out
    assert "should be locked" in captured.out
    assert "disconnect" in captured.out
    assert "notify" in captured.out


def test_show_status_missing_user(module, sample_entries, notif_disabled, capsys):
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=False):
            module.show_status(sample_entries, notif_disabled)

    captured = capsys.readouterr()
    assert "MISSING" in captured.out


def test_show_status_every_day_label(module, notif_disabled, capsys):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri", "sat", "sun"},
        "kill": True,
        "notify": False,
    }

    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True):
            module.show_status([entry], notif_disabled)

    captured = capsys.readouterr()
    assert "every day" in captured.out


def test_show_status_partial_week_label(module, notif_disabled, capsys):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": False,
    }

    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True):
            module.show_status([entry], notif_disabled)

    captured = capsys.readouterr()
    assert "mon, tue, wed, thu, fri" in captured.out


def test_format_days_uses_week_order(module):
    assert module.format_days({"fri", "mon", "sun", "wed"}) == "mon, wed, fri, sun"


def test_show_status_kill_yes(module, notif_disabled, capsys):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon"},
        "kill": True,
        "notify": False,
    }
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False):
            module.show_status([entry], notif_disabled)
    captured = capsys.readouterr()
    assert "disconnect : yes" in captured.out


def test_show_status_kill_no(module, notif_disabled, capsys):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon"},
        "kill": False,
        "notify": False,
    }
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False):
            module.show_status([entry], notif_disabled)
    captured = capsys.readouterr()
    assert "disconnect : no" in captured.out


def test_show_status_empty_entries(module, notif_disabled, capsys):
    with freeze_time("2025-06-02 12:00:00"):
        module.show_status([], notif_disabled)
    captured = capsys.readouterr()
    assert "Current time:" in captured.out


def test_show_status_notifications_enabled(module, notif_enabled, capsys):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon"},
        "kill": True,
        "notify": True,
    }
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False):
            module.show_status([entry], notif_enabled)
    captured = capsys.readouterr()
    assert "notifications: 3 warning(s) every 5 min" in captured.out


def test_show_status_notifications_hidden_when_disabled(module, notif_disabled, capsys):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon"},
        "kill": True,
        "notify": True,
    }
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False):
            module.show_status([entry], notif_disabled)
    captured = capsys.readouterr()
    assert "notifications:" not in captured.out


def test_show_status_includes_config_location_and_parsed_contents(
    module, sample_entries, notif_disabled, capsys, tmp_path
):
    config = tmp_path / "user-curfew.toml"
    config.write_text("# commented out information\n[[user]]\nname = \"ignored\"\n")

    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False):
            module.show_status(sample_entries, notif_disabled, config_path=config)

    captured = capsys.readouterr()
    assert f"Config: {config}" in captured.out
    assert 'name = "alice"' in captured.out
    assert 'name = "bob"' in captured.out
    assert 'days = ["mon", "tue", "wed", "thu", "fri"]' in captured.out
    assert "[notifications]" in captured.out
    assert "commented out information" not in captured.out
    assert 'name = "ignored"' not in captured.out


def test_show_status_always_lock(module, notif_disabled, capsys, tmp_path):
    entry = {
        "name": "alice",
        "lock_time": None,
        "unlock_time": None,
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": False,
        "always_lock": True,
    }
    config = tmp_path / "user-curfew.toml"
    config.write_text('[[user]]\nname = "alice"\nalways_lock = true\n')

    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False):
            module.show_status([entry], notif_disabled, config_path=config)

    captured = capsys.readouterr()
    assert "always_lock = true" in captured.out
    assert "schedule   : always locked" in captured.out
    assert "should be locked" in captured.out


def test_show_status_includes_cron_when_installed(module, sample_entries, notif_disabled, capsys):
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "_cron_status", return_value="installed"):
            module.show_status(sample_entries, notif_disabled, script_path="/usr/local/bin/user-curfew")

    captured = capsys.readouterr()
    assert "cron: installed" in captured.out


def test_show_status_includes_cron_when_not_installed(module, sample_entries, notif_disabled, capsys):
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "_cron_status", return_value="not installed"):
            module.show_status(sample_entries, notif_disabled, script_path="/usr/local/bin/user-curfew")

    captured = capsys.readouterr()
    assert "cron: not installed" in captured.out


def test_cron_status_installed(module):
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = (
        "0 3 * * * /usr/bin/backup\n"
        "*/5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
    )
    with patch("subprocess.run", return_value=proc):
        assert module._cron_status("/usr/local/bin/user-curfew") == "installed"


def test_cron_status_not_installed(module):
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = "0 3 * * * /usr/bin/backup\n"
    with patch("subprocess.run", return_value=proc):
        assert module._cron_status("/usr/local/bin/user-curfew") == "not installed"


def test_cron_status_no_crontab(module):
    proc = MagicMock()
    proc.returncode = 1
    with patch("subprocess.run", return_value=proc):
        assert module._cron_status("/usr/local/bin/user-curfew") == "not installed"


def test_cron_status_no_crontab_command(module):
    with patch("subprocess.run", side_effect=FileNotFoundError):
        assert module._cron_status("/usr/local/bin/user-curfew") == "not installed"


def test_cron_status_skips_commented(module):
    proc = MagicMock()
    proc.returncode = 0
    proc.stdout = (
        "# */5 * * * * /usr/bin/python3 /usr/local/bin/user-curfew --config /etc/user-curfew.toml\n"
    )
    with patch("subprocess.run", return_value=proc):
        assert module._cron_status("/usr/local/bin/user-curfew") == "not installed"

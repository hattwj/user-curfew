from __future__ import annotations

import datetime
from unittest.mock import patch

from freezegun import freeze_time


def test_enforce_user_does_not_exist(module, sample_entry, notif_disabled):
    with patch.object(module, "user_exists", return_value=False), \
         patch.object(module, "is_account_locked") as mock_locked, \
         patch.object(module, "lock_account") as mock_lock, \
         patch.object(module, "unlock_account") as mock_unlock:
        module.enforce([sample_entry], notif_disabled)
        mock_locked.assert_not_called()
        mock_lock.assert_not_called()
        mock_unlock.assert_not_called()


def test_enforce_not_scheduled_day_already_unlocked(module, sample_entry, notif_disabled):
    entry = dict(sample_entry)
    entry["days"] = {"sat", "sun"}

    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_not_called()


def test_enforce_not_scheduled_day_but_locked_should_unlock(module, sample_entry, notif_disabled):
    entry = dict(sample_entry)
    entry["days"] = {"sat", "sun"}

    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_called_once_with("testuser", False)


def test_enforce_inside_lock_window_not_locked_should_lock(module, sample_entry, notif_disabled):
    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([sample_entry], notif_disabled)
            mock_lock.assert_called_once_with("testuser", True, False)
            mock_unlock.assert_not_called()


def test_enforce_inside_lock_window_already_locked_no_action(module, sample_entry, notif_disabled):
    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([sample_entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_not_called()


def test_enforce_outside_lock_window_but_locked_should_unlock(module, sample_entry, notif_disabled):
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([sample_entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_called_once_with("testuser", False)


def test_enforce_outside_lock_window_already_unlocked_no_action(module, sample_entry, notif_disabled):
    with freeze_time("2025-06-02 12:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([sample_entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_not_called()


def test_enforce_after_midnight_inside_window(module, sample_entry, notif_disabled):
    with freeze_time("2025-06-03 02:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([sample_entry], notif_disabled)
            mock_lock.assert_called_once_with("testuser", True, False)


def test_enforce_on_scheduled_day(module, sample_entry, notif_disabled):
    entry = dict(sample_entry)
    entry["days"] = {"mon", "tue", "wed", "thu", "fri"}

    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock:
            module.enforce([entry], notif_disabled)
            mock_lock.assert_called_once()


def test_enforce_on_unscheduled_day_no_lock(module, sample_entry, notif_disabled):
    entry = dict(sample_entry)
    entry["days"] = {"sat", "sun"}

    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_not_called()


def test_enforce_weekend_test(module, notif_disabled):
    entry = {
        "name": "child",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(7, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": False,
    }

    with freeze_time("2025-05-31 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "unlock_account") as mock_unlock:
            module.enforce([entry], notif_disabled)
            mock_lock.assert_not_called()
            mock_unlock.assert_called_once()


def test_enforce_dry_run_passes_flag(module, sample_entry, notif_disabled):
    with freeze_time("2025-06-02 23:30:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock:
            module.enforce([sample_entry], notif_disabled, dry_run=True)
            mock_lock.assert_called_once_with("testuser", True, True)


def test_enforce_multiple_users(module, sample_entries, notif_disabled):
    with freeze_time("2025-06-02 23:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock:
            module.enforce(sample_entries, notif_disabled)
            assert mock_lock.call_count == 2
            assert mock_lock.call_args_list[0].args == ("alice", True, False)
            assert mock_lock.call_args_list[1].args == ("bob", False, False)


def test_enforce_notification_sends_warning(module, notif_enabled):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": True,
    }

    with freeze_time("2025-06-02 22:50:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "lock_account") as mock_lock, \
             patch.object(module, "send_notification") as mock_notify:
            module.enforce([entry], notif_enabled)
            mock_lock.assert_not_called()
            mock_notify.assert_called_once_with("alice", 10, False)


def test_enforce_notification_disabled_globally(module, notif_disabled):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": True,
    }

    with freeze_time("2025-06-02 22:50:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "send_notification") as mock_notify:
            module.enforce([entry], notif_disabled)
            mock_notify.assert_not_called()


def test_enforce_notification_disabled_per_user(module, notif_enabled):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": False,
    }

    with freeze_time("2025-06-02 22:50:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "send_notification") as mock_notify:
            module.enforce([entry], notif_enabled)
            mock_notify.assert_not_called()


def test_enforce_notification_outside_warning_window(module, notif_enabled):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": True,
    }

    with freeze_time("2025-06-02 20:00:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=False), \
             patch.object(module, "send_notification") as mock_notify:
            module.enforce([entry], notif_enabled)
            mock_notify.assert_not_called()


def test_enforce_notification_already_locked(module, notif_enabled):
    entry = {
        "name": "alice",
        "lock_time": datetime.time(23, 0),
        "unlock_time": datetime.time(5, 0),
        "days": {"mon", "tue", "wed", "thu", "fri"},
        "kill": True,
        "notify": True,
    }

    with freeze_time("2025-06-02 22:50:00"):
        with patch.object(module, "user_exists", return_value=True), \
             patch.object(module, "is_account_locked", return_value=True), \
             patch.object(module, "send_notification") as mock_notify:
            module.enforce([entry], notif_enabled)
            mock_notify.assert_not_called()

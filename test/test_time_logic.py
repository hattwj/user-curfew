from __future__ import annotations

import datetime

import pytest


class TestInLockWindow:
    def test_simple_inside_window(self, module):
        now = datetime.time(12, 0)
        lock = datetime.time(9, 0)
        unlock = datetime.time(17, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_simple_before_window(self, module):
        now = datetime.time(8, 0)
        lock = datetime.time(9, 0)
        unlock = datetime.time(17, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_simple_after_window(self, module):
        now = datetime.time(18, 0)
        lock = datetime.time(9, 0)
        unlock = datetime.time(17, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_simple_at_lock_boundary(self, module):
        now = datetime.time(9, 0)
        lock = datetime.time(9, 0)
        unlock = datetime.time(17, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_simple_at_unlock_boundary(self, module):
        now = datetime.time(17, 0)
        lock = datetime.time(9, 0)
        unlock = datetime.time(17, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_simple_exact_window_zero_length(self, module):
        now = datetime.time(9, 0)
        lock = datetime.time(9, 0)
        unlock = datetime.time(9, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_wrapping_inside_lock_period_before_midnight(self, module):
        now = datetime.time(23, 30)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_wrapping_inside_lock_period_after_midnight(self, module):
        now = datetime.time(2, 0)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_wrapping_outside_lock_period(self, module):
        now = datetime.time(12, 0)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_wrapping_at_lock_boundary(self, module):
        now = datetime.time(23, 0)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_wrapping_at_unlock_boundary(self, module):
        now = datetime.time(5, 0)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_wrapping_exact_boundary_before_midnight(self, module):
        now = datetime.time(23, 59)
        lock = datetime.time(23, 0)
        unlock = datetime.time(6, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_wrapping_exact_boundary_after_midnight(self, module):
        now = datetime.time(0, 0)
        lock = datetime.time(23, 0)
        unlock = datetime.time(6, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    def test_wrapping_small_gap_outside(self, module):
        now = datetime.time(20, 0)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_wrapping_small_gap_inside_early_morning(self, module):
        now = datetime.time(4, 59)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) is True

    @pytest.mark.parametrize(
        "hh,mm,expected",
        [
            (0, 0, True),
            (1, 0, True),
            (4, 59, True),
            (5, 0, False),
            (5, 1, False),
            (12, 0, False),
            (22, 59, False),
            (23, 0, True),
            (23, 30, True),
            (23, 59, True),
        ],
    )
    def test_parametrized_23_to_05(self, module, hh, mm, expected):
        now = datetime.time(hh, mm)
        lock = datetime.time(23, 0)
        unlock = datetime.time(5, 0)
        assert module.in_lock_window(now, lock, unlock) == expected

    @pytest.mark.parametrize(
        "hh,mm,expected",
        [
            (8, 59, False),
            (9, 0, True),
            (12, 0, True),
            (16, 59, True),
            (17, 0, False),
            (18, 0, False),
        ],
    )
    def test_parametrized_09_to_17(self, module, hh, mm, expected):
        now = datetime.time(hh, mm)
        lock = datetime.time(9, 0)
        unlock = datetime.time(17, 0)
        assert module.in_lock_window(now, lock, unlock) == expected

    def test_full_day_lock_same_time(self, module):
        now = datetime.time(12, 0)
        lock = datetime.time(0, 0)
        unlock = datetime.time(0, 0)
        assert module.in_lock_window(now, lock, unlock) is False

    def test_wrapping_nearly_full_day(self, module):
        now = datetime.time(12, 0)
        lock = datetime.time(23, 59)
        unlock = datetime.time(23, 58)
        assert module.in_lock_window(now, lock, unlock) is True

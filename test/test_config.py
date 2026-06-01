from __future__ import annotations

import datetime
from pathlib import Path

import pytest


class TestParseTime:
    def test_simple_time(self, module):
        assert module.parse_time("12:30") == datetime.time(12, 30)

    def test_midnight(self, module):
        assert module.parse_time("00:00") == datetime.time(0, 0)

    def test_end_of_day(self, module):
        assert module.parse_time("23:59") == datetime.time(23, 59)

    def test_padded_hours(self, module):
        assert module.parse_time("07:05") == datetime.time(7, 5)

    def test_strips_whitespace(self, module):
        assert module.parse_time("  09:15  ") == datetime.time(9, 15)

    def test_invalid_format_no_colon(self, module):
        with pytest.raises(ValueError, match="invalid time format"):
            module.parse_time("1230")

    def test_extra_seconds_ignored(self, module):
        result = module.parse_time("12:30:45")
        assert result == datetime.time(12, 30)

    def test_invalid_hour_not_a_number(self, module):
        with pytest.raises(ValueError, match="invalid time format"):
            module.parse_time("ab:30")

    def test_invalid_minute_not_a_number(self, module):
        with pytest.raises(ValueError, match="invalid time format"):
            module.parse_time("12:xy")

    def test_empty_string(self, module):
        with pytest.raises(ValueError, match="invalid time format"):
            module.parse_time("")


class TestLoadConfig:
    def test_valid_config(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "23:00"
unlock_time = "05:00"
days = ["mon", "tue", "wed", "thu", "fri"]
kill = true
notify = true
""")
        result = module.load_config(cfg)
        assert len(result["users"]) == 1
        entry = result["users"][0]
        assert entry["name"] == "alice"
        assert entry["lock_time"] == datetime.time(23, 0)
        assert entry["unlock_time"] == datetime.time(5, 0)
        assert entry["days"] == {"mon", "tue", "wed", "thu", "fri"}
        assert entry["kill"] is True
        assert entry["notify"] is True
        assert result["notifications"] == {"enabled": False, "warnings": 3, "interval": 5}

    def test_notifications_section(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[notifications]
enabled = true
warnings = 5
interval = 2

[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
""")
        result = module.load_config(cfg)
        assert result["notifications"] == {"enabled": True, "warnings": 5, "interval": 2}
        assert result["users"][0]["notify"] is True

    def test_notifications_partial(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[notifications]
enabled = true

[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
""")
        result = module.load_config(cfg)
        assert result["notifications"] == {"enabled": True, "warnings": 3, "interval": 5}

    def test_user_notify_defaults_to_global(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[notifications]
enabled = true

[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
""")
        result = module.load_config(cfg)
        assert result["users"][0]["notify"] is True

    def test_user_notify_overrides_global(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[notifications]
enabled = true

[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
notify = false
""")
        result = module.load_config(cfg)
        assert result["users"][0]["notify"] is False

    def test_multiple_users(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"

[[user]]
name = "bob"
lock_time = "23:00"
unlock_time = "07:00"
""")
        result = module.load_config(cfg)
        assert len(result["users"]) == 2
        assert result["users"][0]["name"] == "alice"
        assert result["users"][1]["name"] == "bob"

    def test_default_days(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
""")
        result = module.load_config(cfg)
        assert result["users"][0]["days"] == {"mon", "tue", "wed", "thu", "fri", "sat", "sun"}

    def test_default_kill(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
""")
        result = module.load_config(cfg)
        assert result["users"][0]["kill"] is True

    def test_missing_name(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
lock_time = "22:00"
unlock_time = "06:00"
""")
        with pytest.raises(SystemExit):
            module.load_config(cfg)

    def test_missing_lock_time(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
unlock_time = "06:00"
""")
        with pytest.raises(SystemExit):
            module.load_config(cfg)

    def test_missing_unlock_time(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "22:00"
""")
        with pytest.raises(SystemExit):
            module.load_config(cfg)

    def test_invalid_lock_time(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "not-a-time"
unlock_time = "06:00"
""")
        with pytest.raises(SystemExit):
            module.load_config(cfg)

    def test_invalid_day_names(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
days = ["mon", "funday"]
""")
        with pytest.raises(SystemExit):
            module.load_config(cfg)

    def test_days_case_insensitive(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("""\
[[user]]
name = "alice"
lock_time = "22:00"
unlock_time = "06:00"
days = ["MON", "TUE", "Wed"]
""")
        result = module.load_config(cfg)
        assert result["users"][0]["days"] == {"mon", "tue", "wed"}

    def test_non_existent_file(self, module):
        with pytest.raises(SystemExit):
            module.load_config(Path("/nonexistent/config.toml"))

    def test_empty_user_list(self, module, tmp_path):
        cfg = tmp_path / "test.toml"
        cfg.write_text("# no user entries\n")
        result = module.load_config(cfg)
        assert result["users"] == []

<p align="center">
  <img height="300" src="assets/logo.png">
</p>

Lock/unlock Linux user accounts on a time-based schedule. Intended to run as root via cron every few minutes.

## How it works

No runtime dependencies -- uses only the Python standard library. `requirements.txt` is for development/testing only.

`user-curfew` reads a TOML config file that defines lock schedules for system accounts. When the current time falls inside a user's lock window, the account is locked with `passwd --lock` and active sessions are optionally force-disconnected. When the time is outside the window, the account is unlocked.

Lock windows can wrap across midnight (`lock_time=23:00`, `unlock_time=05:00`), and schedules can be restricted to specific days of the week.

## Requirements

- Python 3.11+
- Linux with `passwd`, `loginctl`, and `pkill` available
- Must be run as root

## Installation

```bash
git clone https://github.com/hattwj/user-curfew.git /opt/user-curfew
sudo /opt/user-curfew/bin/user-curfew --install        # install crontab (every 5 minutes)
sudo /opt/user-curfew/bin/user-curfew --install 10     # install crontab (every 10 minutes)
```

## Configuration

Copy the example config and edit it:

```bash
cp /opt/user-curfew/user-curfew.toml /etc/user-curfew.toml
```

```toml
# Each [[user]] block defines a lock schedule for a system account.
#   name        = the linux username to lock/unlock
#   lock_time   = HH:MM when the account gets locked (24h format)
#   unlock_time = HH:MM when the account gets unlocked (24h format)
#   days        = optional list of weekday names (mon, tue, wed, thu, fri, sat, sun)
#                 defaults to every day if omitted
#   kill        = force-disconnect active sessions at lock time (default: true)

[[user]]
name        = "alice"
lock_time   = "23:00"
unlock_time = "05:00"
days        = ["mon", "tue", "wed", "thu", "fri"]
kill        = true
```

## Usage

```
user-curfew                  # enforce schedules from config
user-curfew --config PATH    # use a specific config file
user-curfew --install [MIN]  # add root crontab entry (default: every 5 min)
user-curfew --dry-run        # show what would happen without changing anything
user-curfew --status         # show current lock state of configured users
user-curfew --verbose        # verbose output
```

## Running tests

```bash
python3 -m venv .venv             # Create venv if it doesn't exist
source .venv/bin/activate         # Activate env 
pip install -r requirements.txt   # Install dependencies
python3 -m pytest test/ -v        # Run tests
```


### Notifications:

Desktop notifications are provided using the notify-send command, and will 
be sent using a command similar to this one:

```sh
systemd-run --machine=$TARGET_USER@.host --user notify-send \
  "Account Curfew" \
  "Your account will be locked in {minutes_left} minute(s)."
```

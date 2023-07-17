# System Desktop Notification Daemon

Send notifications from system services to desktop environment.

Run `sys_desk_notifd.py` in desktop environment (preferably as a `systemd` user service). Then use `notify_deskd.py` to
send notifications from background processes or services running outside desktop environment, or from within desktop
environment.

A sample project which uses `notify_deskd` module to send
notifications: [Systemd Service Status](https://github.com/mirfatif/SystemdSvcStatus).

```
~$ notify_deskd.py -h

Usage:
	notify_deskd.py [OPTIONS]

Send notification from system services to desktop environment.
https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html

Options:
	-h|--help                Show help
	-d|--direct              Send directly to notifications service
	                         (Works only from desktop environment)

	-n|--name                App name
	-r|--replace-id          Notification ID to replace
	-i|--icon                App icon
	-s|--summary             Summary text
	-b|--body                Detailed body text
	-t|--timeout             Notification expiry (seconds)
```

## Installation

Optional dependency: [`priv_exec`](https://github.com/mirfatif/priv_exec). Put the binary on your `$PATH`.

```
~$ export PYTHONUSERBASE=/opt/python_user_base
~$ export PATH=$PYTHONUSERBASE/bin:$PATH

~$ sudo mkdir -p $PYTHONUSERBASE
~$ sudo chown $(id -u) $PYTHONUSERBASE

~$ sudo apt install python3-gi python3-dbus
~$ pip install --ignore-installed --upgrade pip
~$ pip install --upgrade "sys_desk_notifd @ git+https://github.com/mirfatif/SysDeskNotifD"

~$ sudo ln -s $PYTHONUSERBASE/lib/python3.*/site-packages/mirfatif/sys_desk_notifd/etc/systemd/user/sys_desk_notifd.service /etc/systemd/user/
~$ systemctl --user enable sys_desk_notifd.service
~$ systemctl --user start sys_desk_notifd.service

~$ notify_deskd.py -i notification -s 'Test summary' -b 'Test body' -t 5
```

## TODO

Replace legacy [dbus-python](https://dbus.freedesktop.org/doc/dbus-python/)
with [dbus-fast](https://github.com/bluetooth-devices/dbus-fast).

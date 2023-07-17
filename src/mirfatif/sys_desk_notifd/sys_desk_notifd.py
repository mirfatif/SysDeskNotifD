#!/usr/bin/python

import os
import signal
import subprocess
import sys
import traceback

import dbus
import mirfatif.sys_desk_notifd.notify_deskd as notify
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib
from mirfatif.sys_desk_notifd.notify_deskd import Notif


def print_err(msg: str):
    print(msg, file=sys.stderr)


def get_notif_str(d: dict, key: str) -> str:
    if (s := d.get(key)) and isinstance(s, str):
        return s

    if s:
        print_err(f'Bad {key}: {s} ({type(s)})')

    return ''


def get_notif_int(d: dict, key: str, default: int) -> int:
    if (i := d.get(key)) is not None and isinstance(i, int) and (i := int(i)) >= 0:
        return i

    if i := d.get(key):
        print_err(f'Bad {key}: {i} ({type(i)})')

    return default


def handle_dbus_signal(*args):
    if not args:
        return

    if not len(args) == 1 or not isinstance((req := args[0]), dbus.Dictionary):
        print_err(f'Bad request: {type(args)}')
        print(args, file=sys.stderr)
        return

    app_name: str = get_notif_str(req, Notif.APP_NAME)
    replace_id: int = get_notif_int(req, Notif.REPLACE_ID, 0)
    replace_old: str = get_notif_str(req, Notif.REPLACE_OLD)
    app_icon: str = get_notif_str(req, Notif.APP_ICON)
    summary: str = get_notif_str(req, Notif.SUMMARY)
    body: str = get_notif_str(req, Notif.BODY)
    timeout: int = get_notif_int(req, Notif.TIMEOUT, 5)

    if not replace_id and replace_old:
        if nid := notif_ids.get(replace_old):
            replace_id = nid

    nid = notify.notify_direct(
        app_name=app_name,
        replace_id=replace_id,
        app_icon=app_icon,
        summary=summary,
        body=body,
        timeout=timeout,
        user_bus=user_bus
    )

    if replace_old and nid:
        notif_ids[replace_old] = nid


def kill_me(sig: int = None, *_):
    if sys.stdout.isatty():
        print(f'\r')

    if sig:
        print(f'{signal.strsignal(sig)}, exiting...')
    else:
        print('Exiting...')

    if system_bus:
        system_bus.close()

    if user_bus:
        user_bus.close()

    if loop:
        loop.quit()


def set_signal_handlers():
    for sig in (signal.SIGHUP, signal.SIGINT, signal.SIGQUIT, signal.SIGTERM):
        signal.signal(sig, kill_me)
    signal.signal(signal.SIGCHLD, lambda *_: os.wait())


def handle_uncaught_exc(err_type, value, tb):
    print_err(f'Uncaught exception:')
    traceback.print_exception(err_type, value, tb)
    kill_me()


def check_signal_exported():
    try:
        signal_receivers = system_bus.call_blocking(
            'org.freedesktop.DBus',
            '/org/freedesktop/DBus',
            'org.freedesktop.DBus.Debug.Stats',
            'GetAllMatchRules',
            None,
            ()
        )
    finally:
        system_bus.close()

    for i in signal_receivers.items():
        val: dbus.Array = i[1]
        for match in val:
            if match.__contains__(Notif.INTERFACE):
                # print(f'Key: {i[0]}, Sig: {val.signature}, Count: {len(val)}')
                assert len(val) == 1
                print(match)


def main():
    DBusGMainLoop(set_as_default=True)

    global system_bus, user_bus, loop
    system_bus = dbus.SystemBus()

    check_sig_exported = '--check-signal-exported'

    if len(sys.argv) > 1 and sys.argv[1] == check_sig_exported:
        check_signal_exported()
        sys.exit()

    user_bus = dbus.SessionBus()

    sys.excepthook = handle_uncaught_exc
    set_signal_handlers()

    system_bus.add_signal_receiver(handle_dbus_signal, Notif.SIGNAL, Notif.INTERFACE)

    if sys.stdin.isatty() or os.geteuid() == 0:
        if os.geteuid() != 0:
            priv_exec = 'priv_exec -k -u 0 --'
        else:
            priv_exec = ''
        subprocess.call(f'{priv_exec} python3 {sys.argv[0]} {check_sig_exported}'.split())

    print('Listening...')
    sys.stdout.flush()

    loop = GLib.MainLoop()
    loop.run()


system_bus: dbus.SystemBus | None = None
user_bus: dbus.SessionBus | None = None
loop: GLib.MainLoop | None = None
notif_ids: dict[str, int] = {}

if __name__ == '__main__':
    main()

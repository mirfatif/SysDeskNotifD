#!/usr/bin/python

import getopt
import os
import sys
import traceback
import typing

import dbus


class Notif:
    INTERFACE = 'com.mirfatif.SysDeskNotifD'
    SIGNAL = 'Notify'
    SIGNATURE = 'a{sv}'

    APP_NAME = 'app_name'
    REPLACE_ID = 'replace_id'
    REPLACE_OLD = 'replace_old'
    APP_ICON = 'app_icon'
    SUMMARY = 'summary'
    BODY = 'body'
    TIMEOUT = 'timeout'

    PARAMS = [APP_NAME, REPLACE_ID, REPLACE_OLD, APP_ICON, SUMMARY, BODY, TIMEOUT]


# https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html
# https://docs.xfce.org/apps/xfce4-notifyd/spec
# App name, notif id to replace, app icon, summary, body, actions list, hints dict, timeout
NOTIF_SIGN = 'susssasa{sv}i'


def print_exc_line():
    etype, value, tb = sys.exc_info()
    print(''.join(traceback.format_exception_only(etype, value)), file=sys.stderr, end='')


def print_err(msg: str, no_newline: bool = False):
    end = '\n'
    if no_newline:
        end = ''

    print(msg, file=sys.stderr, end=end)


def to_str(lst: list, joiner: str = ' '):
    return joiner.join(str(s) for s in lst)


def notify_proxy(
        app_name: str = None,
        replace_id: int = None,
        replace_old: str = None,
        app_icon: str = None,
        summary: str = None,
        body: str = None,
        timeout: int = None,
        sys_bus: typing.Optional[dbus.SystemBus] = None
):
    args = [app_name, replace_id, replace_old, app_icon, summary, body, timeout]
    notif_args: dict[str, typing.Any] = dict()

    for i in range(len(args)):
        arg = args[i]
        if arg is not None:
            notif_args[Notif.PARAMS[i]] = arg

    msg = dbus.lowlevel.SignalMessage('/', Notif.INTERFACE, Notif.SIGNAL)
    msg.append(notif_args, signature=Notif.SIGNATURE)

    bus = sys_bus or dbus.SystemBus()
    try:
        bus.send_message(msg)
    finally:
        if not sys_bus:
            bus.close()


def notify_direct(
        app_name: str = None,
        replace_id: int = None,
        app_icon: str = None,
        summary: str = None,
        body: str = None,
        timeout: int = None,
        user_bus: typing.Optional[dbus.SessionBus] = None
) -> int:
    bus = user_bus or dbus.SessionBus()

    try:
        # Returns new notif id
        nid = bus.call_blocking(
            'org.freedesktop.Notifications',
            '/org/freedesktop/Notifications',
            'org.freedesktop.Notifications',
            'Notify',
            NOTIF_SIGN,
            (app_name or '', replace_id or 0, app_icon or '', summary or '', body or '', [], [], (timeout or 0) * 1000)
        )
    finally:
        if not user_bus:
            bus.close()

    return nid


def print_usage():
    print(f'\nUsage:\n\t{os.path.basename(sys.argv[0])} [OPTIONS]')
    print('\nSend notification from system services to desktop environment.')
    print('https://specifications.freedesktop.org/notification-spec/notification-spec-latest.html')

    print('\nOptions:')
    print('\t-h|--help                Show help')
    print('\t-d|--direct              Send directly to notifications service')
    print('\t                         (Works only from desktop environment)')

    print('\n\t-n|--name                App name')
    print('\t-r|--replace-id          Notification ID to replace')
    print('\t-i|--icon                App icon')
    print('\t-s|--summary             Summary text')
    print('\t-b|--body                Detailed body text')
    print('\t-t|--timeout             Notification expiry (seconds)\n')


def main():
    opt_help: str = 'help'
    opt_direct: str = 'direct'

    opt_app_name: str = 'name'
    opt_replace_id: str = 'replace-id'
    opt_app_icon: str = 'icon'
    opt_summary: str = 'summary'
    opt_body: str = 'body'
    opt_timeout: str = 'timeout'

    try:
        opts, args = getopt.getopt(
            sys.argv[1:],
            'hdn:r:i:s:b:t:',
            [
                opt_help,
                opt_direct,
                f'{opt_app_name}=',
                f'{opt_replace_id}=',
                f'{opt_app_icon}',
                f'{opt_summary}',
                f'{opt_body}=',
                f'{opt_timeout}='
            ])
    except getopt.GetoptError:
        print_exc_line()
        print_usage()
        sys.exit(1)

    if args:
        print_err(f'Unexpected arguments: {to_str(args)}')
        sys.exit(1)

    def assert_integer(num: str):
        if not num.isdecimal():
            print_err(f'"{num}" is not an integer')
            sys.exit(1)

    direct: bool | None = False
    app_name: str | None = None
    replace_id: int | None = 0
    app_icon: str | None = None
    summary: str | None = None
    body: str | None = None
    timeout: int = 0

    for opt, val in opts:
        if opt == '-h' or opt == f'--{opt_help}':
            print_usage()
            sys.exit(0)
        elif opt == '-d' or opt == f'--{opt_direct}':
            direct = True
        elif opt == '-n' or opt == f'--{opt_app_name}':
            app_name = val
        elif opt == '-r' or opt == f'--{opt_replace_id}':
            assert_integer(val)
            replace_id = int(val)
        elif opt == '-i' or opt == f'--{opt_app_icon}':
            app_icon = val
        elif opt == '-s' or opt == f'--{opt_summary}':
            summary = val
        elif opt == '-b' or opt == f'--{opt_body}':
            body = val
        elif opt == '-t' or opt == f'--{opt_timeout}':
            assert_integer(val)
            timeout = int(val)
        else:
            sys.exit(1)  # Should not happen.

    if direct:
        print(notify_direct(app_name, replace_id, app_icon, summary, body, timeout))
    else:
        notify_proxy(app_name, replace_id, None, app_icon, summary, body, timeout)


if __name__ == '__main__':
    main()

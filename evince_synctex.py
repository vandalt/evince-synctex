#!/usr/bin/python3

# Copyright (C) 2010 Jose Aliste <jose.aliste@gmail.com>
#               2011 Benjamin Kellermann <Benjamin.Kellermann@tu-dresden.de>
#               2018 Mathias Rav <m@git.strova.dk>
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public Licence as published by the Free Software
# Foundation; either version 2 of the Licence, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public Licence for more
# details.
#
# You should have received a copy of the GNU General Public Licence along with
# this program; if not, write to the Free Software Foundation, Inc., 51 Franklin
# Street, Fifth Floor, Boston, MA  02110-1301, USA

"""
Run Evince in SyncTeX mode while continuously building a TeX file.
"""

import os
import re
import sys
import dbus
import shlex
import logging
import argparse
import subprocess
import urllib.parse

parser = argparse.ArgumentParser(
    description=__doc__.lstrip(),
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument('-s', '--build-source', metavar='FILE',
                    dest='source_file',
                    help='Run latexmk to continuously build FILE')
parser.add_argument('-v', '--view-file', metavar='FILE', required=True,
                    dest='pdf_file',
                    help='Open Evince on FILE in synctex mode')
parser.add_argument('cmdline', nargs='+',
                    help='Run command upon Ctrl+Click in Evince')

RUNNING, CLOSED = range(2)

EV_DAEMON_PATH = "/org/gnome/evince/Daemon"
EV_DAEMON_NAME = "org.gnome.evince.Daemon"
EV_DAEMON_IFACE = "org.gnome.evince.Daemon"

EVINCE_PATH = "/org/gnome/evince/Evince"
EVINCE_IFACE = "org.gnome.evince.Application"

EV_WINDOW_IFACE = "org.gnome.evince.Window"


class EvinceWindowProxy:
    """A DBUS proxy for an Evince Window."""
    daemon = None
    bus = None

    def __init__(self, uri, editor, logger):
        assert uri is not None
        assert editor is not None
        assert logger is not None
        self.logger = logger
        self.uri = uri
        self.editor = editor
        self.status = CLOSED
        self.dbus_name = ''
        self._handler = None
        try:
            if EvinceWindowProxy.bus is None:
                EvinceWindowProxy.bus = dbus.SessionBus()

            if EvinceWindowProxy.daemon is None:
                EvinceWindowProxy.daemon = EvinceWindowProxy.bus.get_object(
                    EV_DAEMON_NAME,
                    EV_DAEMON_PATH,
                    follow_name_owner_changes=True)
            EvinceWindowProxy.bus.add_signal_receiver(
                self._on_doc_loaded,
                signal_name="DocumentLoaded",
                dbus_interface=EV_WINDOW_IFACE,
                sender_keyword='sender')
            self._get_dbus_name(False)

        except dbus.DBusException:
            self.logger.debug("Could not connect to the Evince Daemon")

    def _on_doc_loaded(self, uri, **keyargs):
        if uri == self.uri and self._handler is None:
            self.handle_find_document_reply(keyargs['sender'])

    def _get_dbus_name(self, spawn):
        EvinceWindowProxy.daemon.FindDocument(
            self.uri, spawn,
            reply_handler=self.handle_find_document_reply,
            error_handler=self.handle_find_document_error,
            dbus_interface=EV_DAEMON_IFACE)

    def handle_find_document_error(self, error):
        self.logger.debug("FindDocument DBus call has failed")

    def handle_find_document_reply(self, evince_name):
        if evince_name == '':
            self.logger.debug("Did not find an Evince with our document")
            return
        self.logger.debug("Found Evince with our document: %r", evince_name)
        if self._handler is not None:
            handler = self._handler
        else:
            handler = self.handle_get_window_list_reply
        self.dbus_name = evince_name
        self.status = RUNNING
        self.evince = EvinceWindowProxy.bus.get_object(
            self.dbus_name, EVINCE_PATH)
        self.evince.GetWindowList(
            dbus_interface=EVINCE_IFACE,
            reply_handler=handler,
            error_handler=self.handle_get_window_list_error)

    def handle_get_window_list_error(self, e):
        self.logger.debug("GetWindowList DBus call has failed")

    def handle_get_window_list_reply(self, window_list):
        if len(window_list) > 0:
            window_obj = EvinceWindowProxy.bus.get_object(
                self.dbus_name, window_list[0])
            self.window = dbus.Interface(window_obj, EV_WINDOW_IFACE)
            self.window.connect_to_signal("SyncSource", self.on_sync_source)
        else:
            self.logger.debug("GetWindowList returned empty list")

    def on_sync_source(self, input_file, source_link, timestamp):
        path = urllib.parse.unquote(input_file.split("file://")[1])
        line = source_link[0]
        self.logger.debug("Go to %s:%s", path, line)
        cmd = re.sub("%f", shlex.quote(path), self.editor)
        cmd = re.sub("%l", str(line), cmd)
        subprocess.call(cmd, shell=True)


def main(source_file=None, pdf_file=None, cmdline=None,
         configure_logging=True):
    logger = logging.getLogger('evince_synctex')
    if configure_logging:
        logger.setLevel(logging.DEBUG)
        logger.addHandler(logging.StreamHandler())

    if not source_file and not pdf_file:
        raise ValueError('Either source_file or pdf_file must be provided')

    if not pdf_file:
        pdf_file = os.path.splitext(source_file)[0] + '.pdf'

    if not source_file:
        source_file = os.path.splitext(pdf_file)[0] + '.tex'

    if not cmdline:
        cmdline = 'gvim %f +%l'.split()

    import dbus.mainloop.glib
    from gi.repository import GObject as gobject

    pdf_url = 'file://%s' % (
        urllib.parse.quote(os.path.abspath(pdf_file),
                           safe="%/:=&?~#+!$,;'@()*[]"))
    cmdline_string = ' '.join(map(shlex.quote, cmdline))

    build_source_process = None
    if source_file:
        subprocess.check_call(
            ('latexmk', '--synctex=1', '-pdf', source_file))
        build_source_process = subprocess.Popen(
            ('latexmk', '--synctex=1', '-pvc', '-view=none', '-pdf',
             source_file))

    view_process = subprocess.Popen(('evince', pdf_file))

    try:
        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        EvinceWindowProxy.instance = EvinceWindowProxy(
            pdf_url, cmdline_string, logger)
        try:
            gobject.MainLoop().run()
        except KeyboardInterrupt:
            pass
        del EvinceWindowProxy.instance
    finally:
        if build_source_process:
            build_source_process.terminate()
            build_source_process.wait()
        view_process.terminate()
        view_process.wait()


if __name__ == '__main__':
    main(**vars(parser.parse_args()))

'''
command_parser.py - Command parser
'''


import pyndef
import time


PARSER_VERSION = (0, 1)
TIMEOUT = 10


class CommandParser:
    def __init__(self, nfc, ble):
        self._ble = ble
        self._nfc = nfc

        self._last_ch_time = time.monotonic()
        self._input_buffer = b''

        self._current_tag = None
        self._tag_data = b''

    def _cmd_hwver(self):
        ic, ver, rev, sup = self._nfc.firmware_version
        resp = b'HWVER\t{}\t{}\t{}\t{}\n'.format(ic, ver, rev, sup)
        self._ble.uart_write(resp)

    def _cmd_ver(self):
        resp = b'VER\t{}\t{}\n'.format(*PARSER_VERSION)
        self._ble.uart_write(resp)

    def _cmd_unknown(self, cmd):
        resp = b'ERR\tUNKNOWN_CMD\t{}\n'.format(cmd)
        self._ble.uart_write(resp)

    def cmd_scan(self):
        print('CMD SCAN')
        if not self._current_tag or not self._tag_data:
            self._ble.uart_write('SCAN\n')
            return

        uid = b''

        for c in self._current_tag.uid:
            uid += '{:02x}'.format(c)
        uid += b':'
        for c in self._current_tag.serial_number:
            uid += '{:02x}'.format(c)

        resp = b'SCAN\tremovable=yes\tuid=' + uid + b'\t'
        resp += b'text=' + self._tag_data + b'\n'

        self._ble.uart_write(resp)

    def _process_command(self, cmd):
        if '\t' in cmd:
            cmd, args = cmd.split(b'\t', 1)
            args = args.split(b'\t')
        else:
            args = []

        if cmd == b'HWVER':
            self._cmd_hwver()
        elif cmd == b'VER':
            self._cmd_ver()
        elif cmd == b'SCAN':
            self.cmd_scan()

        else:
            self._cmd_unknown(cmd)

    def _process_input(self):
        if not self._input_buffer:
            return False

        nl_idx = self._input_buffer.find(b'\n')

        if nl_idx == -1 and (self._last_ch_time + TIMEOUT) < time.monotonic():
            self._input_buffer += '\n'
            nl_idx = len(self._input_buffer) - 1

        if nl_idx < 0:
            return False

        cmd = self._input_buffer[:nl_idx]
        self._input_buffer = self._input_buffer[nl_idx + 1:]

        self._process_command(cmd)
        return True

    def do_tick(self):
        buf = self._ble.uart_read()
        if buf:
            self._input_buffer += buf
            self._last_ch_time = time.monotonic()

        while self._process_input():
            pass

        tag_info = self._nfc.check_for_tag()

        if (tag_info and
            (not self._current_tag or
                self._current_tag != tag_info)):
            tag_data = self._nfc.read_ntag()
            if tag_data:
                ndef = pyndef.NdefMessage.parse(tag_data).records[0]
                print(ndef)
                lang_len = ndef.payload[0]
                # lang = ndef.payload[1:lang_len + 1]
                tag_data = ndef.payload[lang_len + 1:]
                self._current_tag = tag_info
                self._tag_data = tag_data
                self.cmd_scan()
        if not tag_info and self._current_tag:
            self._current_tag = None
            self._tag_data = b''
            self.cmd_scan()

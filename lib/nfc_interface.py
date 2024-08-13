'''
nfc_interface.py - NFC interface classes

2024 Alice Lutris

Interface to an NFC reader, currently just a PN532.
'''


import board
import busio

from collections import namedtuple
from digitalio import DigitalInOut

from adafruit_pn532.i2c import PN532_I2C
from adafruit_pn532.spi import PN532_SPI
from adafruit_pn532.uart import PN532_UART


FirmwareVersion = namedtuple(
    'FirmwareVersion',
    ['ic', 'ver', 'rev', 'support']
)


NfcTagInfo = namedtuple(
    'NfcTagInfo',
    ['uid', 'serial_number', 'tag_size', 'tag_type']
)


def setup_pins(config: dict) -> dict:
    pins = {}
    for key, value in config['nfc'].items():
        if key.endswith('_pin'):
            if value:
                pins[key] = DigitalInOut(getattr(board, value))
            else:
                pins[key] = None

    return pins


class NfcInterface:
    def __init__(self,
                 interface: busio.I2C | busio.SPI | busio.UART,
                 reset_pin: DigitalInOut | None = None,
                 req_pin: DigitalInOut | None = None,
                 cs_pin: DigitalInOut | None = None,
                 debug: bool = False) -> None:
        self._interface = interface
        self._reset_pin = reset_pin
        self._req_pin = req_pin
        self._debug = debug

        if isinstance(interface, busio.I2C):
            self._pn532 = PN532_I2C(
                self._interface,
                debug=debug,
                reset=reset_pin,
                req=req_pin,
            )
        elif isinstance(interface, busio.SPI):
            if not cs_pin:
                raise ValueError('No CS pin defined, cannot continue.')
            self._pn532 = PN532_SPI(
                self._interface,
                cs_pin,
                debug=debug,
                reset=reset_pin,
            )
        elif isinstance(interface, busio.UART):
            self._pn532 = PN532_UART(
                self._interface,
                debug=debug,
                reset=reset_pin,
            )
        else:
            raise ValueError('Invalid interface')

        self._firmware_version = FirmwareVersion(
            *self._pn532.firmware_version
        )

        self._pn532.SAM_configuration()

    @property
    def firmware_version(self) -> FirmwareVersion:
        return self._firmware_version

    def check_for_tag(self, timeout: float = 1) -> NfcTagInfo | None:
        uid = self._pn532.read_passive_target(timeout=timeout)
        if not uid:
            return None

        tag_info = self._pn532.ntag2xx_read_block(0) or bytearray()
        tag_info += self._pn532.ntag2xx_read_block(1) or bytearray()
        tag_info += self._pn532.ntag2xx_read_block(2) or bytearray()
        tag_info += self._pn532.ntag2xx_read_block(3) or bytearray()

        if len(tag_info) != 16:
            return None

        serial_number = tag_info[:9]
        page_count = tag_info[14] * 2

        if tag_info[12] != 0xe1:
            return None

        # TODO: Add support for MiFare classic cards and other non-ntag cards
        return NfcTagInfo(uid, serial_number, page_count, 'ntag')

    def read_ntag(self,
                  raw: bool = False,
                  timeout: float = 1) -> bytearray | None:
        cc_block = self._pn532.ntag2xx_read_block(3)

        if cc_block is None or cc_block[0] != 0xe1:
            return None

        page_count = cc_block[2] * 2

        tag_data = bytearray()
        ndef_data_size = 0
        for i in range(page_count):
            block = self._pn532.ntag2xx_read_block(4 + i)
            if block is None:
                break
            tag_data += block
            if not raw and i == 0:
                # TODO: Consider looking for the first 0x03 as the data start
                if tag_data[0] != 0x03:
                    return None
                if tag_data[1] < 0xff:
                    ndef_data_size = tag_data[1]
                    tag_data = tag_data[2:]
                else:
                    ndef_data_size = int.from_bytes(tag_data[2:4],
                                                    byteorder='big')
                    tag_data = bytearray()
                ndef_data_size += 1
            if not raw and len(tag_data) > ndef_data_size:
                break

        if not raw:
            tag_data = tag_data[:ndef_data_size]
            if (tag_data and
                (len(tag_data) != ndef_data_size or
                    # Now, if there's 2 NDEF messages here we'll bork; which is
                    # wrong but kinda an edge case for the application.
                    # Properly done multiple NDEF messages should be parsed
                    # until the terminator is found.
                    tag_data[-1] != 0xfe)):
                return None
            tag_data = tag_data[:-1]

        return tag_data

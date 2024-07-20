'''
nfc_interface.py - NFC interface classes

2024 Alice Lutris

Interface to an NFC reader, currently just a PN532.
'''


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

NfcTagData = namedtuple(
    'NfcTagData',
    ['uid', 'tag_size', 'complete', 'tag_data', 'ndef_data']
)


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

    def read_tag(self, timeout: float = 1) -> NfcTagData | None:
        uid = self._pn532.read_passive_target(timeout=timeout)
        print('uid: ', uid)

        if not uid:
            return None

        # TODO: Add support for MiFare cards, other tag data types.

        cc_block = self._pn532.ntag2xx_read_block(3)

        if cc_block is None or cc_block[0] != 0xe1:
            return None

        page_count = cc_block[2] * 2
        ntag_size = page_count * 4

        tag_data = bytearray()
        for i in range(page_count):
            block = self._pn532.ntag2xx_read_block(4 + i)
            if block is None:
                break
            tag_data += block

        complete = (ntag_size == len(tag_data))

        ndef_data = None
        if len(tag_data) >= 4 and tag_data[0] == 0x03:
            if tag_data[1] < 0xff:
                ndef_data_size = tag_data[1]
                ndef_data = tag_data[2:]
            else:
                ndef_data_size = tag_data[2] | (tag_data[3] << 8)
                ndef_data = tag_data[4:]
            ndef_data_size += 1
            if len(ndef_data) >= ndef_data_size:
                ndef_data = ndef_data[:ndef_data_size]
            else:
                ndef_data = None

        return NfcTagData(
            uid, ntag_size, complete, tag_data, ndef_data
        )

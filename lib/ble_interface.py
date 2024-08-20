'''
ble_interface.py - BLE uart interface
'''

import device_info

from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.attributes import Attribute
from adafruit_ble.characteristics import Characteristic
from adafruit_ble.characteristics.int import Uint32Characteristic
from adafruit_ble.characteristics.string import StringCharacteristic
from adafruit_ble.services import Service
from adafruit_ble.services.standard import BatteryService
from adafruit_ble.services.standard.device_info import DeviceInfoService
from adafruit_ble.uuid import VendorUUID


class BytesCharacteristic(Characteristic):
    def __init__(
        self,
        *,
        uuid=None,
        properties=Characteristic.READ,
        read_perm=Attribute.OPEN,
        write_perm=Attribute.OPEN,
        initial_value=None,
    ) -> None:
        super().__init__(
            uuid=uuid,
            properties=properties,
            read_perm=read_perm,
            write_perm=write_perm,
            max_length=512,
            fixed_length=False,
            initial_value=initial_value,
        )

    def __get__(self, obj, cls=None):
        if obj is None:
            return self
        return bytes(super().__get__(obj, cls))

    def __set__(self, obj, value):
        super().__set__(obj, bytes(value))


def hexify_bytes(bs):
    s = ''
    for c in bs:
        s += '{:02x}'.format(c)
    return s


class TapToNfcService(Service):
    uuid = VendorUUID('00000001-0000-1000-1000-00546170546F')

    _status = 0
    _status_char = Uint32Characteristic(
        uuid=VendorUUID('00000001-8002-2000-1000-00546170546F'),
        properties=Characteristic.READ
    )

    _error = StringCharacteristic(
        uuid=VendorUUID('F0000000-4000-2000-1000-00546170546F'),
    )

    _tag_uid = StringCharacteristic(
        uuid=VendorUUID('01000001-4000-2000-1000-00546170546F'),
    )

    _tag_serial = StringCharacteristic(
        uuid=VendorUUID('01000002-4000-2000-1000-00546170546F'),
    )

    _tag_size = Uint32Characteristic(
        uuid=VendorUUID('01000003-8002-2000-1000-00546170546F'),
        properties=Characteristic.READ
    )

    _tag_read = BytesCharacteristic(
        uuid=VendorUUID('01000011-5000-2000-1000-00546170546F'),
    )

    _tag_write = BytesCharacteristic(
        uuid=VendorUUID('02000012-5000-2000-1000-00546170546F'),
        properties=(Characteristic.WRITE_NO_RESPONSE | Characteristic.READ),
    )

    _tag_info = None

    def set_tag_info(self, tag_info):
        if tag_info is None:
            self._tag_info = None
            self._tag_uid = ''
            self._tag_serial = ''
            self._tag_size = 0
            self._tag_read = b''
            self._status &= 0xfffffffe
        else:
            self._tag_info = tag_info
            self._tag_uid = hexify_bytes(tag_info.uid)
            self._tag_serial = hexify_bytes(tag_info.serial_number)
            self._tag_size = tag_info.tag_size
            self._status |= 0x1
        self._status_char = self._status

    def set_tag_data(self, tag_data):
        if not self._tag_info:
            self._tag_read = b''
        else:
            self._tag_read = tag_data

    def report_error(self, err_code, err_str):
        if err_code:
            self._status |= 0x2
            self._error = '{}:{}'.format(err_code, err_str)
        else:
            self._status &= 0xfffffffd
            self._error = ''
        self._status_char = self._status

    def reset(self):
        self._tag_info = None
        self._tag_uid = ''
        self._tag_serial = ''
        self._tag_size = 0
        self._tag_read = b''
        self._tag_write = b''
        self._status = 0
        self._status_char = 0
        self._error = ''


class BleInterface:
    def __init__(self, config):
        self._ble = BLERadio()
        self._ttsvc = TapToNfcService()
        self._ttsvc.reset()
        self._battery = BatteryService()
        self._advt = ProvideServicesAdvertisement(self._ttsvc)
        self._devinfo = DeviceInfoService(**device_info.get_device_info())
        self._ble.name = config['system']['name']

    def start_advertising(self):
        if not self._ble.advertising:
            self._ble.start_advertising(self._advt)

    def stop_advertising(self):
        if self._ble.advertising:
            self._ble.stop_advertising()

    @property
    def advertising(self):
        return self._ble.advertising

    @property
    def connected(self):
        return self._ble.connected

    def set_battery_level(self, level):
        level = max(0, level)
        level = min(100, level)
        self._battery.level = level

    def disconnect(self):
        if self.connected:
            for ble_conn in self._ble.connections:
                ble_conn.disconnect()

    def tag_read(self, tag_info, tag_data):
        self._ttsvc.set_tag_info(tag_info)
        self._ttsvc.set_tag_data(tag_data)

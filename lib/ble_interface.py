'''

'''


from adafruit_ble import BLERadio
from adafruit_ble.advertising.standard import ProvideServicesAdvertisement
from adafruit_ble.services.nordic import UARTService


class BleInterface:
    def __init__(self, config):
        self._ble = BLERadio()
        self._uart = UARTService()
        self._advt = ProvideServicesAdvertisement(self._uart)
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

    def disconnect(self):
        if self.connected:
            for ble_conn in self._ble.connections:
                ble_conn.disconnect()

    def uart_read(self, nbytes=None, wait_timeout=False):
        if not self.connected or not self._uart.in_waiting:
            return None

        if wait_timeout:
            return self._uart.read(nbytes)
        else:
            if nbytes:
                return self._uart.read(min(nbytes, self._uart.in_waiting))
            else:
                return self._uart.read(self._uart.in_waiting)

    def uart_write(self, buf):
        print('writing ', buf)
        if self.connected:
            print('mrp')
            self._uart.write(buf)

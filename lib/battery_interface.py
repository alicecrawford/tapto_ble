'''
battery_interface.py - Battery reporting
'''


import board
import time

from analogio import AnalogIn


class Battery:
    _CHECK_INTERVAL = 10
    _RESOLUTION = 2 ** 16 - 1
    _ANALOG_VREF = 3.3
    _VOLTAGE_DIV = (442 + 160) / 160
    _BAT_ADJ = _ANALOG_VREF / _RESOLUTION * _VOLTAGE_DIV

    def __init__(self):
        self._vbat_sense = AnalogIn(board.BATTERY)
        self._vbat_level = 0
        self._vbat_check_time = -2
        self.update_level()

    # FIXME: I really have to do proper battery calculations here
    def update_level(self):
        t = time.monotonic()
        if t > self._vbat_check_time + self._CHECK_INTERVAL:
            v = self._vbat_sense.value * self._BAT_ADJ
            self._vbat_level = int(round((max(v - 3.4, 0)/0.6) * 100))
            self._vbat_check_time = t
            print('level', self._vbat_level)
            return True
        return False

    @property
    def level(self):
        return self._vbat_level

'''
battery_interface.py - Battery reporting
'''


import board
import time

from analogio import AnalogIn

# FIXME: Yikes, this is all horribly broken.


class Battery:
    _CHECK_INTERVAL = 10
    _RESOLUTION = 2 ** 16 - 1
    _ANALOG_VREF = 3.3
    _VOLTAGE_DIV = (442 + 160) / 160
    _BAT_ADJ = _ANALOG_VREF * _VOLTAGE_DIV

    def __init__(self):
        self._vbat_sense = AnalogIn(board.BATTERY)
        self._vbat_level = 0
        self._vbat_check_time = -2
        self.update_level()

    def update_level(self):
        t = time.monotonic()
        if t > self._vbat_check_time + self._CHECK_INTERVAL:
            v = self._vbat_sense.value * self._BAT_ADJ
            print(v, self._BAT_ADJ)
            self._vbat_level = int(round((max(v - 3.6, 0)/0.6) * 100))
            self._vbat_check_time = t
            print('battery level', self._vbat_level)
            return True
        return False

    @property
    def level(self):
        return self._vbat_level

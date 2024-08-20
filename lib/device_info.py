'''
device_info.py - Get device information
'''


import _bleio
import microcontroller


_SERNO = ''
for c in microcontroller.cpu.uid:
    _SERNO += '{:02x}'.format(c)
for c in _bleio.adapter.address.address_bytes:
    _SERNO += '{:02x}'.format(c)


def get_device_info():
    return {
        'manufacturer': 'TapTo Community/Lutris Labs',
        'software_revision': 'v0.0.2',
        'serial_number': _SERNO,
        'model_number': 'TapToBLE',
        'firmware_revision': '1000',
        'hardware_revision': '1000',
    }

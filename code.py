'''
code.py - Main init and loop code
'''


import json
import supervisor
import time

import interfaces
import nfc_interface
import ble_interface
import battery_interface


def main():
    with open('config.json') as fp:
        config = json.load(fp)

    print('Config loaded, initializing hardware...')

    try:
        intfs = interfaces.setup(config)
        print('Interfaces configured')
        nfc_pins = nfc_interface.setup_pins(config)
        nfc_if_type = config['nfc']['interface']

        nfc = nfc_interface.NfcInterface(
            intfs[nfc_if_type],
            reset_pin=nfc_pins['reset_pin'],
            req_pin=nfc_pins['req_pin'],
            cs_pin=nfc_pins['cs_pin']
        )
        print('NFC reader initialized')
        print('NFC Firmware: IC: {} v{}.{}.{}'.format(*nfc.firmware_version))

    except (ValueError, RuntimeError) as e:
        print('Error in initializing nfc interface: ', e)
        print('Rebooting in 5 seconds...')
        time.sleep(5)
        supervisor.reload()

    ble = ble_interface.BleInterface(config)
    battery = battery_interface.Battery()
    current_tag = None

    while True:
        if not ble.advertising and not ble.connected:
            ble.start_advertising()

        if battery.update_level():
            ble.set_battery_level(battery.level)

        tag_info = nfc.check_for_tag()
        if tag_info != current_tag:
            if tag_info:
                tag_data = nfc.read_ntag()
                if tag_data:
                    ble.tag_read(tag_info, tag_data)
                    current_tag = tag_info
            else:
                ble.tag_read(tag_info, None)
                current_tag = tag_info


main()

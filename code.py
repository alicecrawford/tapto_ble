'''

'''


import json
import supervisor
import time

import interfaces
import nfc_interface
import ble_interface

import pyndef


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

    last_tag = None
    last_tag_data = None
    tag_loop_counter = 0

    while True:
        if not ble.advertising and not ble.connected:
            ble.start_advertising()

        tag_info = nfc.check_for_tag()

        # If the last tag is still on the reader we just sleep for a second
        if last_tag and tag_info == last_tag and last_tag_data:
            tag_loop_counter = 0
            time.sleep(1)
            continue

        if not tag_info:
            if last_tag:
                if tag_loop_counter >= 1:
                    last_tag = None
                    last_tag_data = None
                    tag_loop_counter = 0
                    print('Tag removed')
                else:
                    tag_loop_counter += 1
            continue

        print('Found tag: ', tag_info)
        last_tag = tag_info
        tag_loop_counter = 0
        tag_data = nfc.read_ntag()
        last_tag_data = tag_data
        if not tag_data:
            print('No tag data read')
        else:
            ndef = pyndef.NdefMessage.parse(tag_data)
            ble.uart_write(str(ndef))
            print('Ndef data:')
            print(ndef)


main()

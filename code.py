'''

'''


import json
import supervisor
import time

import interfaces
import nfc_interface


def main():
    with open('config.json') as fp:
        config = json.load(fp)

    try:
        intfs = interfaces.setup(config)
        nfc_pins = nfc_interface.setup_pins(config)
        nfc_if_type = config['nfc']['interface']

        nfc = nfc_interface.NfcInterface(
            intfs[nfc_if_type],
            reset_pin=nfc_pins['reset_pin'],
            req_pin=nfc_pins['req_pin'],
            cs_pin=nfc_pins['cs_pin']
        )
    except (ValueError, RuntimeError) as e:
        print('Error in initializing nfc interface: ', e)
        print('Rebooting in 5 seconds...')
        time.sleep(5)
        supervisor.reload()

    while True:
        print('Checking for tag...')
        tag_info = nfc.check_for_tag()
        if tag_info:
            print('Found tag: ', tag_info)
            tag_data = nfc.read_ntag()
            print(tag_data)
            if not tag_data:
                print('No tag data read')
            else:
                s = ''
                for i, c in enumerate(tag_data):
                    s += '{:02x}'.format(c)
                    i += 1
                    if (i % 32) == 0:
                        s += '\n'
                    elif (i % 4) == 0:
                        s += '   '
                    elif (i % 2) == 0:
                        s += ' '
                print(s)
                print('Tag len: ', len(tag_data))
        else:
            print('No tag found.')


main()

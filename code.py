'''

'''


import json

import interfaces
import nfc_interface


def main():
    with open('config.json') as fp:
        config = json.load(fp)

    intfs = interfaces.setup(config)
    nfc_pins = nfc_interface.setup_pins(config)
    nfc_if_type = config['nfc']['interface']

    nfc = nfc_interface.NfcInterface(
        intfs[nfc_if_type],
        reset_pin=nfc_pins['reset_pin'],
        req_pin=nfc_pins['req_pin'],
        cs_pin=nfc_pins['cs_pin']
    )

    while True:
        print('nfc read: ', nfc.read_tag())


main()

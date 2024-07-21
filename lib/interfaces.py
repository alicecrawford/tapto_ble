'''
interfaces.py - Setup interfaces

Alice Lutris - 2024

This module will create applicable interfaces based on what
is specified in config.json
'''


import board
import busio


def _setup_i2c(settings: dict) -> busio.I2C | None:
    if not settings['enabled'] == 'true':
        return None

    return busio.I2C(
        getattr(board, settings['scl']),
        getattr(board, settings['sda'])
    )


def _setup_spi(settings: dict) -> busio.SPI | None:
    if not settings['enabled'] == 'true':
        return None

    return busio.SPI(
        getattr(board, settings['sck']),
        getattr(board, settings['mosi']),
        getattr(board, settings['miso'])
    )


def _setup_uart(settings: dict) -> busio.UART | None:
    if not settings['enabled'] == 'true':
        return None

    return busio.UART(
        getattr(board, settings['tx']),
        getattr(board, settings['rx']),
        baudrate=settings['baudrate'],
        timeout=settings['timeout']
    )


def setup(config: dict) -> dict:
    interfaces = {
        'i2c': None,
        'spi': None,
        'uart': None
    }
    for if_name, if_settings in config['interfaces'].items():
        if if_name == 'i2c':
            interfaces['i2c'] = _setup_i2c(if_settings)
        elif if_name == 'spi':
            interfaces['spi'] = _setup_spi(if_settings)
        elif if_name == 'uart':
            interfaces['uart'] = _setup_uart(if_settings)
    return interfaces

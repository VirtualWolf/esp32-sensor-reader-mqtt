import gc
import uasyncio as asyncio
from machine import UART
import ustruct as struct
import logger

async def read_data(rx_pin):
    logger.log('Initialising UART bus')

    if isinstance(rx_pin, str):
        rx_pin = int(rx_pin)

    uart = UART(1, 9600)
    uart.init(9600, bits=8, parity=None, rx=rx_pin, timeout=250)

    count = 0

    while count < 30:
        logger.log(f'Warming sensor up, reading #{count} of 30')

        await _read_sensor(uart)
        count = count + 1
        await asyncio.sleep(1)

    logger.log('Finished warming up')

    data = await _read_sensor(uart)

    if data is None:
        await asyncio.sleep(1)
        await _read_sensor(uart)

    logger.log(data)
    logger.log('Turning off UART bus')

    uart.deinit()

    return data

async def _read_sensor(uart):
    buffer = []

    data = uart.read(32)

    if data is None:
        logger.log('No data received')

        return

    data = list(data)

    gc.collect()

    buffer += data

    while buffer and buffer[0] != 0x42:
        buffer.pop(0)

    # Avoid an overrun if all bad data
    if len(buffer) > 200:
        buffer = []

    if len(buffer) < 32:
        logger.log('Buffer length > 32')

        return

    if buffer[1] != 0x4d:
        logger.log('Second element of buffer was not 0x4d')

        buffer.pop(0)

        return

    frame_len = struct.unpack(">H", bytes(buffer[2:4]))[0]

    gc.collect()

    if frame_len != 28:
        buffer = []

        logger.log('Frame length was not 28')

        return

    # In order:
    #  - PM1.0 standard
    #  - PM2.5 standard
    #  - PM10 standard
    #  - PM1.0 environmental
    #  - PM2.5 environmental
    #  - PM10 environmental
    #  - Particles > 0.3m / 0.1L air
    #  - Particles > 0.5um / 0.1L air
    #  - Particles > 1.0um / 0.1L air
    #  - Particles > 2.5um / 0.1L air
    #  - Particles > 5.0um / 0.1L air
    #  - Particles > 10um / 0.1L air
    #  - Skip
    #  - Checksum
    frame = struct.unpack(">HHHHHHHHHHHHHH", bytes(buffer[4:]))

    check = sum(buffer[0:30])

    if check != frame[-1]:
        buffer = []

        logger.log('Checksums don\'t match')

        return

    buffer = buffer[32:]

    return {
        'pm_1_0': frame[3],
        'pm_2_5': frame[4],
        'pm_10': frame[5],

        'particles_0_3um': frame[6],
        'particles_0_5um': frame[7],
        'particles_1_0um': frame[8],
        'particles_2_5um': frame[9],
        'particles_5_0um': frame[10],
        'particles_10um': frame[11],
    }

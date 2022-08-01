import ntptime
from mqtt_as import MQTTClient, config
from machine import Pin, reset
from config import config
import uasyncio as asyncio
import sensor
import logger

async def wifi_handler(state):
    led = Pin(13, Pin.OUT)

    if state:
        logger.log('WiFi is up.')
        led.value(1)
    else:
        logger.log('WiFi is down.')
        led.value(0)
    await asyncio.sleep(1)

async def main(client):
    try:
        await client.connect()

        ntptime.host = config['ntp_server']

        logger.log('Setting time using server %s' % (ntptime.host))

        ntptime.settime()
    except OSError:
        logger.log('Connection failed.')
        return

    while True:
        await sensor.read_sensor(client)

config['wifi_coro'] = wifi_handler
config['clean'] = False

client = MQTTClient(config)

async def weekly_reboot():
    while True:
        await asyncio.sleep(604800) # 1 week in seconds
        logger.log('Weekly reboot!')
        reset()

try:
    asyncio.create_task(weekly_reboot())

    asyncio.run(main(client))
    asyncio.run(weekly_reboot())
finally:  # Prevent LmacRxBlk:1 errors.
    client.close()
    asyncio.new_event_loop()

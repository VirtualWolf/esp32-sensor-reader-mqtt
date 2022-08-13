import ntptime
from mqtt_as import MQTTClient, config
from machine import Pin, WDT
from config import config
import uasyncio as asyncio
import sensor
import logger

# Automatically reboot after one week, given here in milliseconds
wdt = WDT(timeout=604800000)

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

try:
    asyncio.run(main(client))
finally:  # Prevent LmacRxBlk:1 errors.
    client.close()
    asyncio.new_event_loop()

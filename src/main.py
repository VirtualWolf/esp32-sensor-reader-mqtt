import ntptime
from mqtt_as import MQTTClient, config as mqtt_config
from machine import Pin, Timer, reset
from config import config
import uasyncio as asyncio
import sensor
import updater
import logger

def set_time(timer = None):
    ntptime.host = config['ntp_server']

    logger.log('Setting time using server %s' % (ntptime.host))

    try:
        ntptime.settime()
    except OSError:
        logger.log('Failed to contact NTP server at %s' % config['ntp_server'])
        reset()

async def wifi_handler(state):
    led = Pin(13, Pin.OUT)

    if state:
        logger.log('Wifi and MQTT broker are up')
        led.value(1)
    else:
        logger.log('Wifi or MQTT broker is down')
        led.value(0)
    await asyncio.sleep(1)

async def main(client):
    try:
        await client.connect()
    except OSError:
        logger.log('Connection to wifi or MQTT broker failed')
        reset()

    # Run an initial NTP sync on board start
    ntptime.settime()

    # Synchronise with the NTP server once a day
    set_time_timer = Timer(0)
    set_time_timer.init(mode=Timer.PERIODIC, period=86400000, callback=set_time)

    for coroutine in (updater.subscribe, updater.messages):
        asyncio.create_task(coroutine(client))

    while True:
        await sensor.read_sensor(client)

mqtt_config['wifi_coro'] = wifi_handler
mqtt_config['clean'] = False
mqtt_config['queue_len'] = 10

client = MQTTClient(mqtt_config)

try:
    asyncio.run(main(client))
finally:  # Prevent LmacRxBlk:1 errors.
    client.close()
    asyncio.new_event_loop()

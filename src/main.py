import ntptime
from mqtt import MQTTClient, config as mqtt_config
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

def set_connection_status(state):
    led = Pin(13, Pin.OUT)

    if state:
        logger.log('Wifi and MQTT broker are up')
        led.value(0)
    else:
        logger.log('Wifi or MQTT broker is down')
        led.value(1)

async def up(client):
    while True:
        await client.up.wait()
        client.up.clear()
        set_connection_status(True)

        update_topic = 'commands/%s/update' % config['client_id']
        logger.log('Subscribing to %s' % update_topic)
        await client.subscribe(update_topic, 1)

        get_config_topic = 'commands/%s/get_config' % config['client_id']
        logger.log('Subscribing to %s' % get_config_topic)
        await client.subscribe(get_config_topic, 1)

async def down(client):
    while True:
        await client.down.wait()  # Pause until connectivity changes
        client.down.clear()
        set_connection_status(False)

set_connection_status(False)

async def main(client):
    try:
        await client.connect()
    except OSError:
        logger.log('Connection to wifi or MQTT broker failed')
        reset()

    # Run an initial NTP sync on board start
    ntptime.host = config['ntp_server']
    ntptime.settime()

    # Synchronise with the NTP server once a day
    set_time_timer = Timer(0)
    set_time_timer.init(mode=Timer.PERIODIC, period=86400000, callback=set_time)

    for coroutine in (up, down, updater.messages):
        asyncio.create_task(coroutine(client))

    while True:
        await sensor.read_sensor(client)

mqtt_config['clean'] = config['clean']
mqtt_config['queue_len'] = 10

client = MQTTClient(mqtt_config)

try:
    asyncio.run(main(client))
finally:  # Prevent LmacRxBlk:1 errors.
    client.close()
    asyncio.new_event_loop()

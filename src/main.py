import ntptime
from machine import Pin, Timer, reset
import uasyncio as asyncio
from mqtt import MQTTClient, config as mqtt_config
from config import config
import sensor
import admin
import logger

def set_time():
    ntptime.host = config['ntp_server']

    logger.log(f'Setting time using server {ntptime.host}')

    try:
        ntptime.settime()
    except OSError:
        logger.log(f'Failed to contact NTP server at {ntptime.host}')
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

        logger.log(f"Subscribing to {config['commands_topic']}")
        await client.subscribe(config['commands_topic'], 1)

        await logger.publish_log_message({'message': f"Client '{config['client_id']}' is online!"}, client=client)

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

    for coroutine in (up, down, admin.messages):
        asyncio.create_task(coroutine(client))

    while True:
        await sensor.read_sensor(client)

mqtt_config['queue_len'] = 10

client = MQTTClient(mqtt_config)

try:
    asyncio.run(main(client))
finally:  # Prevent LmacRxBlk:1 errors.
    client.close()
    asyncio.new_event_loop()

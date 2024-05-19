import asyncio
import ntptime
from machine import Pin, Timer, reset
from neopixel import NeoPixel
from mqtt import MQTTClient, config as mqtt_config
from lib.ota import rollback, status
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
    # When the wifi and MQTT broker are both successfully connected turn the LED off
    if state:
        logger.log('Wifi and MQTT broker are up')

        if config['neopixel_pin'] is not None:
            pixel.fill((0,0,0))
            pixel.write()
        else:
            led.value(0)

    # Either wifi or the MQTT broker are down to so turn the LED on
    else:
        logger.log('Wifi or MQTT broker is down')

        if config['neopixel_pin'] is not None:
            pixel.fill((100,0,0))
            pixel.write()
        else:
            led.value(1)

async def up(client):
    while True:
        await client.up.wait()
        client.up.clear()
        set_connection_status(True)

        logger.log(f"Subscribing to {config['commands_topic']}")
        await client.subscribe(config['commands_topic'], 1)

        await logger.publish_log_message({'status': "online"}, client=client, retain=True)

        # Verify that the board supports OTA updates
        if status.ready() is True:
            # Everything has started up successfully so we can cancel the automatic rollback on reboot
            rollback.cancel()

async def down(client):
    while True:
        await client.down.wait()  # Pause until connectivity changes
        client.down.clear()
        set_connection_status(False)

# The onboard NeoPixel on the Adafruit QT Py doesn't have power enabled by default so we need to turn it on first
if config['neopixel_pin'] is not None and config['neopixel_power_pin'] is not None:
    power_pin = Pin(config['neopixel_power_pin'], Pin.OUT)
    power_pin.on()

# Use the onboard NeoPixel LED for status indicators if the appropriate configuration options are set
if config['neopixel_pin'] is not None:
    pin = Pin(config['neopixel_pin'], Pin.OUT)
    pixel = NeoPixel(pin, 1)
else:
    led = Pin(config['led_pin'], Pin.OUT)

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

    for coroutine in (up, down, admin.messages, sensor.read_sensors):
        asyncio.create_task(coroutine(client))

    while True:
        await asyncio.sleep(30)

mqtt_config['queue_len'] = 10

mqtt_client = MQTTClient(mqtt_config)

try:
    asyncio.run(main(mqtt_client))
finally:  # Prevent LmacRxBlk:1 errors.
    mqtt_client.close()
    asyncio.new_event_loop()

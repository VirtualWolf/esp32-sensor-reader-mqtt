import asyncio
import json
import ntptime
from machine import Pin, reset
from neopixel import NeoPixel
from mqtt import MQTTClient, config as mqtt_config
from lib.ota import rollback, status
from config import config
import sensor
import output_device
import admin
import logger

async def sync_ntp(client):
    while True:
        try:
            ntptime.settime()

            await logger.publish_log_message({'message': f'Successfully synced with NTP server {ntptime.host}'}, client=client)
        except OSError as e:
            await logger.publish_error_message(error={'error': f'Failed to contact NTP server at {ntptime.host}'}, exception=e, client=client)

        # Sync once per day
        await asyncio.sleep(86400)

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

        # For any output devices as opposed to sensors, we need to subscribe to the relevant topics here
        # so the subscription is re-established even after wifi or MQTT broker outages
        if 'outputs' in config:
            try:
                piicodev_config = next(item for item in config['outputs'] if item['type'] == 'piicodev_rgb')
            except StopIteration:
                piicodev_config = None

            if piicodev_config is not None:
                logger.log(f"Subscribing to LED state topic at {piicodev_config['state_topic']}")
                await client.subscribe(piicodev_config['state_topic'], 1)

                for location in piicodev_config['topics']:
                    logger.log(f"Subscribing to {location['topic']}")
                    await client.subscribe(location['topic'], 1)

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

async def messages(client):
    async for tpc, msg, retained in client.queue:
        try:
            topic = tpc.decode()
            payload = json.loads(msg.decode())

            if topic == config['commands_topic']:
                await admin.messages(client=client, payload=payload)
            else:
                await output_device.update_outputs(client=client, topic=topic, payload=payload)

        except ValueError as e:
            await logger.publish_error_message(error={'error': f'Received payload was not JSON: {msg.decode()}'}, exception=e, client=client)
        except Exception as e:
            await logger.publish_error_message(error={'error': 'Something went wrong'}, exception=e, client=client)

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

    for coroutine in (up, down, messages, sensor.read_sensors, sync_ntp):
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

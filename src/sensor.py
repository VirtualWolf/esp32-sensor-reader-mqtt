from binascii import unhexlify
import gc
import utime
from machine import Pin
import dht
import ujson
import uasyncio as asyncio
import logger
from config import read_configuration

temperature = 0
humidity = 0
timestamp = 0

c = read_configuration()

async def read_sensor(client):
    global temperature
    global humidity
    global timestamp

    while True:
        logger.log('Reading sensor...')

        try:
            sensor = dht.DHT22(Pin(26))
            sensor.measure()

            temperature = sensor.temperature()
            humidity = sensor.humidity()

            if temperature == 0 and humidity == 0:
                # Embedded systems epoch is 2000-01-01 00:00:00 UTC, so we need
                # to add 946684800 seconds onto it to turn it into a UNIX epoch
                # timestamp
                timestamp = (utime.time() + 946684800) * 1000

                logger.log('First reading, values are %s˚ & %s%%' % (temperature, humidity))
            else:
                if abs(temperature - temperature) > 0.3:
                    logger.log('Skipping because difference is too large. Currently %s, got %s' % (temperature, temperature))
                else:
                    temperature = sensor.temperature()
                    humidity = sensor.humidity()
                    timestamp = (utime.time() + 946684800) * 1000

                    logger.log('Sensor read at %s, new values: %s & %s%%' % (timestamp, temperature, humidity))

                    current_data = ujson.dumps({
                        "timestamp": timestamp,
                        "temperature": temperature,
                        "humidity": humidity
                    })

                    await client.publish(c['topic'], current_data, qos = 1, retain = True)

            gc.collect()

        except Exception as e:
            logger.log('Failed to read sensor: '  + str(e))

        await asyncio.sleep(30)

import gc
import utime
from machine import Pin, WDT, I2C
import dht
import ujson
import uasyncio as asyncio
import logger
from config import config
import bme280_float as bme280

async def read_sensor(client):
    if config['disable_watchdog'] is not True:
        wdt = WDT(timeout=120000)

    temperature = 0
    humidity = 0
    pressure = 0
    dew_point = 0
    timestamp = 0

    while True:
        logger.log('Reading sensor...')

        try:
            if config['sensor_type'] == 'dht22':
                sensor = dht.DHT22(Pin(26))
                sensor.measure()

                temperature = sensor.temperature()
                humidity = sensor.humidity()

                temperature = sensor.temperature()
                humidity = sensor.humidity()
                timestamp = (utime.time() + 946684800) * 1000

                logger.log(f'Sensor read at {timestamp}, new values: {temperature} & {humidity}%')

                current_data = {
                    "timestamp": timestamp,
                    "temperature": temperature,
                    "humidity": humidity
                }

                await publish_sensor_reading(reading=current_data, client=client)

                if config['disable_watchdog'] is not True:
                    wdt.feed()

            elif config['sensor_type'] == 'bme280':
                i2c = I2C(0, sda=Pin(config['sda_pin']), scl=Pin(config['scl_pin']))

                # The "address" value is 119 on both an Adafruit HUZZAH32 as well
                # as the Unexpected Maker Feather S2, and not the default 118 that
                # the BME280 library assumes.
                # The address to use can be determined with i2c.scan()
                sensor = bme280.BME280(i2c=i2c, address=119)

                (temperature, pressure, humidity) = sensor.read_compensated_data()
                dew_point = sensor.dew_point
                timestamp = (utime.time() + 946684800) * 1000

                logger.log(f'Sensor read at {timestamp}, new values: {temperature}, {humidity}%, and {pressure} hPa. Dew point is {dew_point}')

                current_data = {
                    "timestamp": timestamp,
                    "temperature": temperature,
                    "humidity": humidity,
                }

                if config['enable_bme280_additional_data'] is True:
                    current_data.update({
                        "dew_point": dew_point,
                        "pressure": pressure/100
                    })

                await publish_sensor_reading(reading=current_data, client=client)

                if config['disable_watchdog'] is not True:
                    wdt.feed()

            gc.collect()

        except Exception as e:
            await logger.publish_log_message(message={'error': f'Failed to read sensor, error was: {str(e)}'}, client=client)

        await asyncio.sleep(30)

async def publish_sensor_reading(reading, client):
    await client.publish(config['topic'], ujson.dumps(reading), qos = 1, retain = True)

import gc
import time
import json
import asyncio
from machine import Pin, WDT, I2C
import dht
import logger
from config import config
from lib import ens160
from lib import bme280_float as bme280
from lib import pms5003

try:
    sensor_dht22 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'dht22')
except StopIteration:
    sensor_dht22 = False

try:
    sensor_bme280 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'bme280')
except StopIteration:
    sensor_bme280 = False

try:
    sensor_pms5003 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'pms5003')
except StopIteration:
    sensor_pms5003 = False

try:
    sensor_ens160 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'ens160')
except StopIteration:
    sensor_ens160 = False

if sensor_bme280 or sensor_ens160:
    i2c = I2C(0, sda=Pin(config['sda_pin']), scl=Pin(config['scl_pin']), timeout=50000)

if config['disable_watchdog'] is not True:
    if sensor_pms5003:
        wdt = WDT(timeout=600000)
    else:
        wdt = WDT(timeout=120000)

if sensor_ens160:
    # Global variables to hold the temperature and humidity for calibrating the ENS160
    temperature_calibration = 25
    humidity_calibration = 50

gc.collect()



async def read_sensors(client):
    logger.log('Reading sensors...')

    if sensor_dht22:
        asyncio.create_task(_read_dht22(client=client))

    if sensor_bme280:
        asyncio.create_task(_read_bme280(client=client))

    if sensor_pms5003:
        asyncio.create_task(_read_pms5003(client=client))

    if sensor_ens160:
        asyncio.create_task(_read_ens160(client=client))



async def _read_dht22(client):
    global temperature_calibration
    global humidity_calibration

    sensor = dht.DHT22(Pin(sensor_dht22['rx_pin']))

    while True:
        try:
            sensor.measure()

            temperature = sensor.temperature()
            humidity = sensor.humidity()
            timestamp = (time.time() + 946684800) * 1000

            if sensor_ens160:
                temperature_calibration = temperature
                humidity_calibration = humidity

            logger.log(f'Sensor read at {timestamp}, new values: {temperature} & {humidity}%')

            current_data = {
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity
            }

            await publish_sensor_reading(reading=current_data, client=client, topic=sensor_dht22['topic'])

            if config['disable_watchdog'] is not True:
                wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        gc.collect()
        await asyncio.sleep(30)



async def _read_bme280(client):
    global temperature_calibration
    global humidity_calibration

    sensor = bme280.BME280(i2c=i2c, address=sensor_bme280['i2c_address'])

    while True:
        try:
            (temperature, pressure, humidity) = sensor.read_compensated_data()
            dew_point = sensor.dew_point
            timestamp = (time.time() + 946684800) * 1000

            if sensor_ens160:
                temperature_calibration = temperature
                humidity_calibration = humidity

            logger.log(f'Sensor read at {timestamp}, new values: {temperature}C, {humidity}%, and {pressure} Pa. Dew point is {dew_point}')

            current_data = {
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity,
            }

            if sensor_bme280['enable_additional_data'] is True:
                current_data.update({
                    "dew_point": dew_point,
                    "pressure": pressure/100
                })

            await publish_sensor_reading(reading=current_data, client=client, topic=sensor_bme280['topic'])

            if config['disable_watchdog'] is not True:
                wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        gc.collect()
        await asyncio.sleep(30)



async def _read_pms5003(client):
    while True:
        try:
            current_data = await pms5003.read_data(client=client, rx_pin=sensor_pms5003['rx_pin'])
            current_data['timestamp'] = (time.time() + 946684800) * 1000

            await publish_sensor_reading(reading=current_data, client=client, topic=sensor_pms5003['topic'])

            if config['disable_watchdog'] is not True:
                wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        await asyncio.sleep(180)
        gc.collect()



async def _read_ens160(client):
    global temperature_calibration
    global humidity_calibration

    sensor = ens160.ENS160(i2c=i2c, address=sensor_ens160['i2c_address'], temperature=temperature_calibration, humidity=humidity_calibration)

    while True:
        try:
            (aqi, tvoc, eco2) = sensor.get_readings()
            timestamp = (time.time() + 946684800) * 1000

            logger.log('Sensor read at {}. AQI {}, TVOC {}, ECO2 {}'.format(timestamp, aqi, tvoc, eco2))

            if aqi == 0:
                await logger.publish_log_message({'message': 'Received 0 reading for AQI, skipping'}, client=client)
            else:
                current_data = {
                    'timestamp': timestamp,
                    'aqi': aqi,
                    'tvoc': tvoc,
                    'eco2': eco2,
                }

                await publish_sensor_reading(reading=current_data, client=client, topic=sensor_ens160['topic'])

                if config['disable_watchdog'] is not True:
                    wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        gc.collect()
        await asyncio.sleep(30)



async def publish_sensor_reading(reading, client, topic):
    await client.publish(topic, json.dumps(reading), qos=1, retain=True)

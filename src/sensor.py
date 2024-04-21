import gc
import utime
from machine import Pin, WDT, I2C
import dht
import ujson
import uasyncio as asyncio
import logger
from config import config
import bme280_float as bme280
import ens160
import pms5003

# Global variables to hold the temperature and humidity for calibrating the ENS160
temperature_calibration = 25
humidity_calibration = 50

async def read_sensor(client):
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
        i2c = I2C(0, sda=Pin(config['sda_pin']), scl=Pin(config['scl_pin']))

    if config['disable_watchdog'] is not True:
        if sensor_pms5003:
            wdt = WDT(timeout=600000)
        else:
            wdt = WDT(timeout=120000)

    gc.collect()

    while True:
        logger.log('Reading sensors...')

        global temperature_calibration
        global humidity_calibration

        try:
            if sensor_dht22:
                sensor = dht.DHT22(Pin(sensor_dht22['rx_pin']))
                sensor.measure()

                temperature = sensor.temperature()
                humidity = sensor.humidity()
                timestamp = (utime.time() + 946684800) * 1000

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

            if sensor_bme280:
                sensor = bme280.BME280(i2c=i2c, address=sensor_bme280['i2c_address'])

                (temperature, pressure, humidity) = sensor.read_compensated_data()
                dew_point = sensor.dew_point
                timestamp = (utime.time() + 946684800) * 1000

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

            if sensor_pms5003:
                current_data = await pms5003.read_data(client)
                current_data['timestamp'] = (utime.time() + 946684800) * 1000

                await publish_sensor_reading(reading=current_data, client=client, topic=sensor_pms5003['topic'])

                if config['disable_watchdog'] is not True:
                    wdt.feed()

            if sensor_ens160:
                sensor = ens160.ENS160(i2c=i2c, address=sensor_ens160['i2c_address'], temperature=temperature_calibration, humidity=humidity_calibration)

                (aqi, tvoc, eco2) = sensor.get_readings()
                timestamp = (utime.time() + 946684800) * 1000

                logger.log('Sensor read at {}. AQI {}, TVOC {}, ECO2 {}'.format(timestamp, aqi, tvoc, eco2))

                current_data = {
                    'timestamp': timestamp,
                    'aqi': aqi,
                    'tvoc': tvoc,
                    'eco2': eco2,
                }

                await publish_sensor_reading(reading=current_data, client=client, topic=sensor_ens160['topic'])

                if config['disable_watchdog'] is not True:
                    wdt.feed()

            gc.collect()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        if sensor_pms5003:
            await asyncio.sleep(180)
        else:
            await asyncio.sleep(30)

async def publish_sensor_reading(reading, client, topic):
    await client.publish(topic, ujson.dumps(reading), qos=1, retain=True)

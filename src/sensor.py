from math import log
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
from lib import sht30
from lib import pms5003
from lib import vl53l1x

try:
    sensor_dht22 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'dht22')
except StopIteration:
    sensor_dht22 = False

try:
    sensor_bme280 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'bme280')
except StopIteration:
    sensor_bme280 = False

try:
    sensor_sht30 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'sht30')
    sensor_sht30['heater_on_count'] = 0
    sensor_sht30['heater_enabled_at'] = 0
except StopIteration:
    sensor_sht30 = False

try:
    sensor_pms5003 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'pms5003')
except StopIteration:
    sensor_pms5003 = False

try:
    sensor_ens160 = next(sensor for sensor in config['sensors'] if sensor['type'] == 'ens160')
except StopIteration:
    sensor_ens160 = False

try:
    sensor_vl53l1x = next(sensor for sensor in config['sensors'] if sensor['type'] == 'vl53l1x')
except StopIteration:
    sensor_vl53l1x = False

if sensor_bme280 or sensor_sht30 or sensor_ens160 or sensor_vl53l1x:
    i2c = I2C(0, sda=Pin(config['sda_pin']), scl=Pin(config['scl_pin']), timeout=50000)

if config['disable_watchdog'] is not True:
    if sensor_pms5003:
        # The PMS5003 is only read every three minutes to prolong the sensor lifetime so
        # the watchdog timeout needs to be several times that, rather than two minutes
        # for the other sensors
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

    if sensor_sht30:
        asyncio.create_task(_read_sht30(client=client))

    if sensor_pms5003:
        asyncio.create_task(_read_pms5003(client=client))

    if sensor_ens160:
        asyncio.create_task(_read_ens160(client=client))

    if sensor_vl53l1x:
        asyncio.create_task(_read_vl53l1x(client=client))



async def _read_dht22(client):
    global temperature_calibration
    global humidity_calibration

    sensor = dht.DHT22(Pin(sensor_dht22['rx_pin']))

    while True:
        try:
            sensor.measure()

            temperature = sensor.temperature()
            humidity = sensor.humidity()
            dew_point = calculate_dew_point(temperature=temperature, humidity=humidity)
            timestamp = generate_timestamp()

            if sensor_ens160:
                temperature_calibration = temperature
                humidity_calibration = humidity

            logger.log(f'Sensor read at {timestamp}, new values: {temperature} & {humidity}%. Dew point is {dew_point}')

            current_data = {
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity
            }

            if sensor_dht22.get('enable_dew_point') is True:
                current_data.update({
                    'dew_point': dew_point
                })

            await publish_sensor_reading(reading=current_data, client=client, topic=sensor_dht22['topic'])

            # The PMS5003 sensor is only read once every three minutes and the watchdog timeout when a PMS5003 is configured is
            # ten minutes, so we need to skip the every-30-seconds WDT feed for this sensor if there is also a PMS5003 attached
            if config['disable_watchdog'] is not True and not sensor_pms5003:
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
            timestamp = generate_timestamp()

            if sensor_ens160:
                temperature_calibration = temperature
                humidity_calibration = humidity

            logger.log(f'Sensor read at {timestamp}, new values: {temperature}C, {humidity}%, and {pressure} Pa. Dew point is {dew_point}')

            if sensor_bme280.get('enable_pressure_only') is True:
                current_data = {
                    "timestamp": timestamp,
                    "pressure": pressure/100
                }
            else:
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

            # The PMS5003 sensor is only read once every three minutes and the watchdog timeout when a PMS5003 is configured is
            # ten minutes, so we need to skip the every-30-seconds WDT feed for this sensor if there is also a PMS5003 attached
            if config['disable_watchdog'] is not True and not sensor_pms5003:
                wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        gc.collect()
        await asyncio.sleep(30)



async def _read_sht30(client):
    global temperature_calibration
    global humidity_calibration

    sensor = sht30.SHT30(i2c=i2c, address=sensor_sht30['i2c_address'])

    while True:
        try:
            (temperature, humidity) = sensor.measure()
            dew_point = calculate_dew_point(temperature, humidity)
            timestamp = generate_timestamp()

            if sensor_ens160:
                temperature_calibration = temperature
                humidity_calibration = humidity

            logger.log(f'Sensor read at {timestamp}, new values: {temperature}C, {humidity}%. Dew point is {dew_point}')

            current_data = {
                "timestamp": timestamp,
                "temperature": temperature,
                "humidity": humidity
            }

            if sensor_sht30.get('enable_dew_point') is True:
                current_data.update({'dew_point': dew_point})

            await publish_sensor_reading(reading=current_data, client=client, topic=sensor_sht30['topic'])

            is_heater_enabled = sensor.is_heater_enabled()

            HIGH_HUMIDITY = 95

            if is_heater_enabled is None:
                sensor_status = sensor.status()
                await logger.publish_log_message(message={'message':f'Received unexpected response from heater status check: {sensor_status}'}, client=client)

            # Initial state of high humidity, heater not on, and hasn't been on in the last five minutes
            if humidity > HIGH_HUMIDITY and sensor_sht30['heater_on_count'] == 0 and (timestamp - sensor_sht30['heater_enabled_at']) > 300000 and is_heater_enabled is False:
                await logger.publish_log_message(message={'message': f'Humidity is {humidity}, enabling heater'}, client=client)

                sensor.enable_heater()
                sensor_sht30['heater_on_count'] = sensor_sht30['heater_on_count'] + 1
                sensor_sht30.update({
                    'heater_enabled_at': timestamp
                })

            # Humidity has reduced so we can turn the heater off regardless of how long it's been on
            elif humidity <= HIGH_HUMIDITY and is_heater_enabled is True:
                await logger.publish_log_message(message={'message': f'Humidity is {humidity}, disabling heater'}, client=client)

                sensor.disable_heater()
                sensor_sht30['heater_on_count'] = 0

            # Heater is on but humidity is still high and the maximum heater count hasn't been reached
            elif humidity > HIGH_HUMIDITY and is_heater_enabled is True and 0 < sensor_sht30['heater_on_count'] < 5:
                await logger.publish_log_message(message={'message': f"Humidity is {humidity}, incrementing heater_on_count to {sensor_sht30['heater_on_count']}"}, client=client)

                sensor_sht30['heater_on_count'] = sensor_sht30['heater_on_count'] + 1

            # The heater is on and has been on for the last five readings so we'll turn it off again
            elif is_heater_enabled is True and sensor_sht30['heater_on_count'] >= 5:
                await logger.publish_log_message(message={'message': f'Humidity is {humidity}, heater_on_count has reached 5, disabling heater'}, client=client)

                sensor.disable_heater()
                sensor_sht30['heater_on_count'] = 0

            # The PMS5003 sensor is only read once every three minutes and the watchdog timeout when a PMS5003 is configured is
            # ten minutes, so we need to skip the every-30-seconds WDT feed for this sensor if there is also a PMS5003 attached
            if config['disable_watchdog'] is not True and not sensor_pms5003:
                wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        gc.collect()
        await asyncio.sleep(30)



async def _read_pms5003(client):
    while True:
        try:
            current_data = await pms5003.read_data(rx_pin=sensor_pms5003['rx_pin'])

            if current_data is None:
                await logger.publish_error_message(error={'error': 'No valid data'}, client=client)

                continue

            current_data['timestamp'] = generate_timestamp()

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
            timestamp = generate_timestamp()

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

                # The PMS5003 sensor is only read once every three minutes and the watchdog timeout when a PMS5003 is configured is
                # ten minutes, so we need to skip the every-30-seconds WDT feed for this sensor if there is also a PMS5003 attached
                if config['disable_watchdog'] is not True and not sensor_pms5003:
                    wdt.feed()

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        gc.collect()
        await asyncio.sleep(30)



async def _read_vl53l1x(client):
    sensor = vl53l1x.VL53L1X(i2c=i2c, address=sensor_vl53l1x['i2c_address'])

    last_trigger = 0
    triggered = False

    while True:
        try:
            distance = sensor.read()

            if sensor.status != 'OK':
                continue

            timestamp = generate_timestamp()

            # If the threshold is breached AND it's not currently triggered AND the last trigger timestamp is more than the ignore period, send a trigger message
            if distance < sensor_vl53l1x['trigger_threshold_mm'] and triggered is False and (timestamp - last_trigger > (sensor_vl53l1x['ignore_trigger_period'] * 1000)):
                await logger.publish_log_message({'message': 'Distance threshold breached'}, client=client)

                await publish_sensor_reading(reading={'timestamp': timestamp, 'triggered': True}, client=client, topic=sensor_vl53l1x['topic'])

                gc.collect()

                last_trigger = timestamp
                triggered = True

            # If the threshold is breached but it's already been triggered, update the last trigger timestamp so the ignore period remains current
            elif distance < sensor_vl53l1x['trigger_threshold_mm'] and triggered is True:
                last_trigger = timestamp

            # If the threshold is no longer breached AND it's currently triggered AND the last trigger time is greater than the ignore period, reset back to false
            elif distance > sensor_vl53l1x['trigger_threshold_mm'] and triggered is True and (last_trigger < timestamp - (sensor_vl53l1x['ignore_trigger_period'] * 1000)):
                await logger.publish_log_message({'message': 'Distance threshold not breached in last period, resetting trigger'}, client=client)

                await publish_sensor_reading(reading={'timestamp': timestamp, 'triggered': False}, client=client, topic=sensor_vl53l1x['topic'])

                triggered = False

        except Exception as e:
            await logger.publish_error_message(error={'error': 'Failed to read sensor'}, exception=e, client=client)

        await asyncio.sleep_ms(50)



def generate_timestamp():
    return (time.time() + 946684800) * 1000



async def publish_sensor_reading(reading, client, topic):
    await client.publish(topic, json.dumps(reading), qos=1, retain=True)



# Thanks to https://gist.github.com/sourceperl/45587ea99ff123745428?permalink_comment_id=5119362#gistcomment-5119362
def calculate_dew_point(temperature, humidity):
    a = 17.625
    b = 243.04
    alpha = log(humidity/100.0) + ((a * temperature) / (b + temperature))

    return (b * alpha) / (a - alpha)

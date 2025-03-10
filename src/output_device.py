from machine import Pin, WDT, I2C
import logger
from config import config
from lib import piicodev_rgb

try:
    output_piicodev_rgb = next(output for output in config['outputs'] if output['type'] == 'piicodev_rgb')
except StopIteration:
    output_piicodev_rgb = False



if output_piicodev_rgb:
    i2c = I2C(0, sda=Pin(config['sda_pin']), scl=Pin(config['scl_pin']), timeout=50000)
    output_piicodev_rgb['is_on'] = True

    output_piicodev_rgb['board'] = piicodev_rgb.PiicoDev_RGB(i2c=i2c, bright=output_piicodev_rgb.get('led_brightness', 20))
    output_piicodev_rgb['board'].pwrLED(False)
    output_piicodev_rgb['current_led_states'] = [[0,0,0], [0,0,0], [0,0,0]]

if config['disable_watchdog'] is not True:
    wdt = WDT(timeout=120000)



async def update_outputs(client, topic, payload):
    if output_piicodev_rgb:
        await _update_piicodev_rgb(client=client, topic=topic, payload=payload)



async def _update_piicodev_rgb(client, topic, payload):
    colours = {
        'red':          [255,0,0],
        'dark_orange':  [255,80,0],
        'orange':       [255,140,0],
        'yellow':       [255,180,0],
        'green':        [0,255,0],
        'light_green':  [100,255,100],
        'cyan':         [0,255,255],
        'blue':         [0,140,255],
        'dark_blue':    [0,0,255],
        'dark_purple':  [80,0,255],
        'purple':       [140,0,255],
        'fuchsia':      [255,0,255],
        'pink':         [255,0,120],
    }

    if config['disable_watchdog'] is not True:
        wdt.feed()

    # Handle the general on or off state of the LEDs
    if topic == output_piicodev_rgb['state_topic'] and 'is_on' in payload and isinstance(payload['is_on'], bool):
        if payload['is_on']:
            await logger.publish_log_message(message={'message': 'Enabling LEDs'}, client=client)
            output_piicodev_rgb['is_on'] = True

            for (led_number, colour) in enumerate(output_piicodev_rgb['current_led_states']):
                _set_piicodev_rgb_led_colour(led_number, colour)

            output_piicodev_rgb['board'].show()

        else:
            output_piicodev_rgb['board'].clear()
            await logger.publish_log_message(message={'message': 'Disabling LEDs'}, client=client)
            output_piicodev_rgb['is_on'] = False

        return

    led_number = next(
        index for (index, item) in enumerate(output_piicodev_rgb['topics']) if item['topic'] == topic
    )

    received_value = payload.get(output_piicodev_rgb['topics'][led_number]['value'], None)

    if received_value is None:
        return

    thresholds = output_piicodev_rgb['topics'][led_number]['thresholds']
    threshold_colours = output_piicodev_rgb['topics'][led_number]['colours']

    for (index, item) in enumerate(thresholds[:-1]):
        current_threshold, next_threshold = item, thresholds[index + 1]

        if current_threshold <= received_value < next_threshold:
            colour = colours[threshold_colours[index]]

            output_piicodev_rgb['current_led_states'][led_number] = colour
            _set_piicodev_rgb_led_colour(led_number, colour)

            break
        else:
            colour = colours[threshold_colours[-1]]

            output_piicodev_rgb['current_led_states'][led_number] = colour
            _set_piicodev_rgb_led_colour(led_number, colour)

    if output_piicodev_rgb['is_on'] is False:
        return

    output_piicodev_rgb['board'].show()

def _set_piicodev_rgb_led_colour(led_number, colour):
    output_piicodev_rgb['board'].setPixel(led_number, colour)

import gc
import ujson
from machine import reset
from logger import log

async def messages(client):
    async for topic, msg, retained in client.queue:
        payload = ujson.loads(msg.decode())

        if 'update_code' in payload and payload['update_code'] == True:
            start_code_update()

        if 'config' in payload:
            start_config_update(payload['config'])



def start_config_update(incoming_config):
    log('Triggered a configuration update!')

    with open('config.json', 'r') as file:
        current_config = ujson.load(file)

    log('Current configuration:')
    log(current_config)

    current_config.update(incoming_config)

    log('Updated configuration:')
    log(current_config)

    with open('config.json', 'w') as file:
        ujson.dump(current_config, file)

    reset()

def start_code_update():
    log('Triggered an update check!')

    gc.collect()

    import senko

    files = [
        'senko/__init__.py',
        'senko/senko.py',
        'mqtt.py',
        'config.py',
        'logger.py',
        'main.py',
        'sensor.py',
        'updater.py'
    ]

    OTA = senko.Senko(
        user='VirtualWolf',
        repo='esp32-sensor-reader-mqtt',
        branch='main',
        working_dir='src',
        files=files)

    if OTA.update():
        log('Updated to the latest version! Rebooting...')
        reset()
    else:
        log('Already the latest version!')

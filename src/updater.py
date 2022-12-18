import gc
from machine import reset
from config import config
from logger import log

async def subscribe(client):
    update_topic = 'updates/%s' % config['client_id']

    log('Subscribing to %s' % update_topic)

    while True:
        await client.up.wait()
        client.up.clear()
        await client.subscribe(update_topic, 1)

async def messages(client):
    async for topic, msg, retained in client.queue:
        if msg.decode() == 'update':
            gc.collect()

            import senko

            files = [
                'senko/__init__.py',
                'senko/senko.py',
                'config.py',
                'logger.py'
                'main.py',
                'mqtt_as.py',
                'sensor.py',
                'updater.py'
            ]

            OTA = senko.Senko(user='VirtualWolf', repo='esp32-sensor-reader-mqtt', working_dir='src', files=files)

            if OTA.update():
                log('Updated to the latest version! Rebooting...')
                reset()
            else:
                log('Already the latest version!')

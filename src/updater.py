import gc
from machine import reset
from config import config
from logger import log

async def messages(client):
    async for topic, msg, retained in client.queue:
        if msg.decode() == 'update':
            log('Triggering an update check!')

            gc.collect()

            import senko

            files = [
                'senko/__init__.py',
                'senko/senko.py',
                'mqtt_as.py',
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

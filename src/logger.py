import utime
import ujson
from config import config

def log(message):
    year, month, day, hour, minute, second, weekday, yearday = utime.gmtime()

    now = '{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}'.format(year, month, day, hour, minute, second)

    log_line = '[%s] %s' % (now, message)

    print(log_line)

async def publish_log_message(message, client, retain=False):
    if 'config' in message:
        message['config'].update({'wifi_pw': '********'})

        if message['config'].get('github_token') is not None:
            message['config'].update({'github_token': '********'})

    log(message)
    await client.publish(config['logs_topic'], ujson.dumps(message), qos = 1, retain=retain)

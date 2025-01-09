import io
import sys
import gc
import time
import json
from config import config

def get_current_time():
    year, month, day, hour, minute, second, weekday, yearday = time.gmtime()

    return '{}-{:02d}-{:02d}T{:02d}:{:02d}:{:02d}Z'.format(year, month, day, hour, minute, second)

def log(message):
    log_line = '[%s] %s' % (get_current_time(), message)

    print(log_line)

async def publish_log_message(message, client, retain=False):
    if 'config' in message:
        message['config'].update({'wifi_pw': '********'})

        if message['config'].get('github_token') is not None:
            message['config'].update({'github_token': '********'})

    message['timestamp'] = get_current_time()

    log(message)
    await client.publish(config['logs_topic'], json.dumps(message), qos=1, retain=retain)

async def publish_error_message(error, client, exception=None):
    if exception is not None:
        buf = io.StringIO()
        sys.print_exception(exception, buf)

        error['traceback'] = buf.getvalue()

    error['timestamp'] = get_current_time()

    gc.collect()

    log(error)
    await client.publish(config['logs_topic'], json.dumps(error), qos=1)

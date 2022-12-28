import gc
import hmac
from uhashlib import sha256
import ujson
import config
from machine import reset
from logger import log

async def messages(client):
    c = config.read_configuration()

    async for topic, msg, retained in client.queue:
        gc.collect()

        if topic.decode() == 'commands/%s/update' % c['client_id']:
            try:
                payload = ujson.loads(msg.decode())

                if 'update_code' in payload and payload['update_code'] == True:
                    start_code_update()
                elif 'config' in payload:
                    start_config_update(payload.get('config'), payload.get('signature'))
            except:
                pass

        if topic.decode() == 'commands/%s/get_config' % c['client_id']:
            with open('config.json', 'r') as file:
                current_config = ujson.load(file)

            current_config.update({'wifi_pw': '********'})

            if current_config.get('signing_secret') is not None:
                current_config.update({'signing_secret': '********'})

            await client.publish('logs/%s' % c['client_id'], ujson.dumps(current_config), qos = 1)

def start_config_update(incoming_config, signature = None):
    c = config.read_configuration()

    if c.get('signing_secret') is not None:
        if is_signature_valid(incoming_config, signature):
            log('Signature is valid, updating config')

            update_config(incoming_config)
        else:
            log('Signature was not valid')
            return
    else:
        log('Updating config')
        update_config(incoming_config)

def update_config(incoming_config):
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
    c = config.read_configuration()
    log('Triggered an update!')

    gc.collect()

    import update_from_github
    OTA = update_from_github.UpdateFromGitHub(
        username='VirtualWolf',
        github_token=c['github_token'],
        repository='esp32-sensor-reader-mqtt',
        working_dir='src',
    )

    OTA.update()
    log('Update successful, restarting...')
    reset()

def is_signature_valid(content, signature = None):
    c = config.read_configuration()

    stringified_content = ujson.dumps(content, separators=(',',':'))

    hash = hmac.new(
        bytes(c.get('signing_secret'), 'UTF-8'),
        bytes(stringified_content, 'UTF-8'),
        digestmod=sha256
    )

    if hash.hexdigest() == signature:
        return True
    else:
        return False

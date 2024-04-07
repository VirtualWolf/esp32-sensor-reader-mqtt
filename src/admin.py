from platform import platform
import gc
import hmac
from uhashlib import sha256
import ujson
from machine import reset
from config import config
from update_from_github import UpdateFromGitHub
from logger import publish_log_message

async def messages(client):
    async for topic, msg, retained in client.queue:
        gc.collect()

        if topic.decode() == config['commands_topic']:
            try:
                payload = ujson.loads(msg.decode())

                if 'command' in payload:
                    if payload['command'] == 'get_config':
                        await get_config(client)

                    if payload['command'] == 'get_system_info':
                        await get_system_info(client)

                    elif payload['command'] == 'update_config' and 'config' in payload:
                        await start_config_update(incoming_config=payload.get('config'), signature=payload.get('signature'), client=client)

                    elif payload['command'] == 'update_code':
                        await start_code_update(client)

            except ValueError:
                await publish_log_message(message={'error': f'Received payload was not JSON: {msg.decode()}'}, client=client)



async def get_config(client):
    with open('config.json', 'r') as file:
        current_config = ujson.load(file)

    await publish_log_message(message={'config': current_config}, client=client)



async def get_system_info(client):
    system_info = {
        "micropython_version": platform(),
        "free_memory": gc.mem_free()
    }

    await publish_log_message(message=system_info, client=client)



async def start_config_update(incoming_config, client, signature = None):
    if config['signing_secret'] is not None:
        if is_signature_valid(incoming_config, signature):
            await publish_log_message(message={'message': 'Signature is valid, proceeding with update...'}, client=client)

            await update_config(incoming_config, client)
        else:
            await publish_log_message(message={'message': 'Signature is not valid'}, client=client)

            return
    else:
        await update_config(incoming_config, client)



async def update_config(incoming_config, client):
    with open('config.json', 'r') as file:
        current_config = ujson.load(file)

    config_key = next(iter(incoming_config.keys()))
    config_value = next(iter(incoming_config.values()))

    required_config_keys = ['client_id', 'server', 'port', 'ssid', 'wifi_pw', 'topic']

    if config_key in required_config_keys and not config_value:
        await publish_log_message(message={
            'error': f"Cannot unset required configuration '{config_key}'",
            'config': current_config
        }, client=client)

        return

    if not config_value:
        del current_config[config_key]
    else:
        current_config.update(incoming_config)

    with open('config.json', 'w') as file:
        ujson.dump(current_config, file)

    await publish_log_message(message={
        'message': 'Configuration updated, restarting board...',
        'config': current_config
    }, client=client)

    reset()



async def start_code_update(client):
    await publish_log_message(message={'message': 'Beginning code update from GitHub...'}, client=client)

    gc.collect()

    OTA = UpdateFromGitHub(
        username=config['github_username'],
        api_token=config['github_token'],
        repository=config['github_repository'],
        ref=config['github_ref'],
        client=client,
    )

    await OTA.update()

    await publish_log_message(message={'message': 'Code update successful, restarting board...'}, client=client)

    reset()



def is_signature_valid(content, signature = None):
    stringified_content = ujson.dumps(content, separators=(',',':'))

    generated_hash = hmac.new(
        bytes(config['signing_secret'], 'UTF-8'),
        bytes(stringified_content, 'UTF-8'),
        digestmod=sha256
    )

    return generated_hash.hexdigest() == signature

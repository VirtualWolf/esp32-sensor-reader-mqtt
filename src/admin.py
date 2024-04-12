from platform import platform
import gc
import ujson
from machine import reset
from config import config
from update_from_github import Updater
from logger import publish_log_message, publish_error_message

async def messages(client):
    async for topic, msg, retained in client.queue:
        gc.collect()

        try:
            payload = ujson.loads(msg.decode())

            if 'command' in payload:
                if payload['command'] == 'get_config':
                    await get_config(client)

                if payload['command'] == 'get_system_info':
                    await get_system_info(client)

                elif payload['command'] == 'update_config' and 'config' in payload:
                    await update_config(incoming_config=payload.get('config'), client=client)

                elif payload['command'] == 'update_code':
                    await start_code_update(client)
        except ValueError as e:
            await publish_error_message(message=f'Received payload was not JSON: {msg.decode()}', exception=e, client=client)
        except Exception as e:
            await publish_error_message(message='Something went wrong', exception=e, client=client)


async def get_config(client):
    with open('config.json', 'r') as file:
        current_config = ujson.load(file)

    await publish_log_message(message={'config': current_config}, client=client)



async def get_system_info(client):
    try:
        with open('.version', 'r') as file:
            commit = file.read()
    except OSError:
        commit = 'No .version file found!'


    system_info = {
        "version": commit,
        "micropython_version": platform(),
        "free_memory": gc.mem_free()
    }

    await publish_log_message(message=system_info, client=client)



async def update_config(incoming_config, client):
    try:
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


        if config_value == '':
            del current_config[config_key]
        else:
            current_config.update(incoming_config)

        with open('config.json', 'w') as file:
            ujson.dump(current_config, file)

        await publish_log_message(message={
            'message': 'Configuration updated, restarting board...',
            'config': current_config,
            'status': 'offline',
        }, client=client)

        reset()
    except Exception as e:
        await publish_error_message(message='Failed to update configuration', exception=e, client=client)


async def start_code_update(client):
    try:
        await publish_log_message(message={'message': 'Beginning code update from GitHub...'}, client=client)

        gc.collect()

        OTA = Updater(
            username=config['github_username'],
            api_token=config['github_token'],
            repository=config['github_repository'],
            ref=config['github_ref'],
            client=client,
        )

        await OTA.update()

        await publish_log_message(message={
            'message': 'Code update successful, restarting board...',
            'status': 'offline',
        }, client=client)

        reset()
    except Exception as e:
        await publish_error_message(message='Failed to run OTA.update()', exception=e, client=client)

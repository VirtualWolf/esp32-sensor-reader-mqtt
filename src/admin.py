from platform import platform
import gc
import ujson
import uos
from machine import reset
import ota.update
import ota.status
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

                elif payload['command'] == 'update_firmware' and 'firmware' in payload:
                    await start_firmware_update(firmware=payload.get('firmware'), client=client)

        except ValueError as e:
            await publish_error_message(error={'error': f'Received payload was not JSON: {msg.decode()}'}, exception=e, client=client)
        except Exception as e:
            await publish_error_message(error={'error': 'Something went wrong'}, exception=e, client=client)


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

    filesystem_stats = uos.statvfs('/')
    block_size = filesystem_stats[0]
    total_blocks = filesystem_stats[2]
    free_blocks = filesystem_stats[3]

    free_memory = gc.mem_free()

    system_info = {
        "version": commit,
        "micropython_version": platform(),
        "free_memory": f'{(free_memory/1024):.2f}KB',
        "total_space": f'{(block_size * total_blocks)/1024:.0f}KB',
        "free_space": f'{(block_size * free_blocks)/1024:.0f}KB',
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
        await publish_error_message(error={'error': 'Failed to update configuration'}, exception=e, client=client)


async def start_code_update(client):
    try:
        await publish_log_message(message={'message': 'Beginning code update from GitHub...'}, client=client)

        gc.collect()

        config_updater = Updater(
            username=config['github_username'],
            api_token=config['github_token'],
            repository=config['github_repository'],
            ref=config['github_ref'],
            client=client,
        )

        await config_updater.update()

        await publish_log_message(message={
            'message': 'Code update successful, restarting board...',
            'status': 'offline',
        }, client=client)

        reset()
    except Exception as e:
        await publish_error_message(error={'error': 'Failed to run update code'}, exception=e, client=client)

async def start_firmware_update(firmware, client):
    if ota.status.ready() is not True:
        await publish_error_message(error={'error': 'Board cannot be updated over the air, make sure it has been flashed with an OTA-enabled image'}, client=client)
        return

    if firmware is None:
        await publish_error_message(error={'error': 'Missing payload'}, client=client)
        return

    url = firmware.get('url')
    size = firmware.get('size')
    sha256 = firmware.get('sha256')

    if url is None or sha256 is None or size is None:
        await publish_error_message(error={'error': "url, size, or sha256 field(s) missing from payload"}, client=client)
        return

    await publish_log_message(message={
        'message': f'Beginning firmware update from {url}...',
        'update_status': 'updating',
    }, client=client)

    try:
        gc.collect()

        ota.update.from_file(url, sha=sha256, length=size, reboot=False)

        await publish_log_message(message={
            'message': f'Sucessfully updated firmware from {url}, restarting...',
            'update_status': 'updated',
            'status': 'offline',
        }, client=client)

        reset()
    except ValueError as e:
        await publish_error_message(error={
            'error': 'Failed to update firmware, OTA returned an error',
            'update_status': 'failed',
        }, exception=e, client=client)
    except Exception as e:
        await publish_error_message(error={
            'error': 'Failed to update firmware, something went wrong',
            'update_status': 'failed',
        }, exception=e, client=client)

import json
from mqtt import config as mqtt_config

with open('config.json', 'r') as file:
    c = json.load(file)

# Settings for the MQTT library
mqtt_config['client_id']                     = c.get('client_id')
mqtt_config['server']                        = c.get('server')
mqtt_config['port']                          = c.get('port')
mqtt_config['ssid']                          = c.get('ssid')
mqtt_config['wifi_pw']                       = c.get('wifi_pw')
mqtt_config['will']                          = f"logs/{c.get('client_id')}", '{"status": "offline"}', True, 1

config = {}

# Settings for sensor reading
config['sensors']                       = c.get('sensors', [])
config['sda_pin']                       = c.get('sda_pin', 23)
config['scl_pin']                       = c.get('scl_pin', 22)

# Optional settings
config['ntp_server']                    = c.get('ntp_server', 'time.cloudflare.com')
config['disable_watchdog']              = c.get('disable_watchdog', False)


# Settings for GitHub updates
config['github_token']                  = c.get('github_token', None)
config['github_username']               = c.get('github_username', 'VirtualWolf')
config['github_repository']             = c.get('github_repository', 'esp32-sensor-reader-mqtt')
config['github_ref']                    = c.get('github_ref', 'main')

# MQTT topics to subscribe to for receiving commands and emitting logs
config['commands_topic']                = f"commands/{c.get('client_id')}"
config['logs_topic']                    = f"logs/{c.get('client_id')}"

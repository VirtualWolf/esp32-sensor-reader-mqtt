import ujson
from mqtt import config

with open('config.json', 'r') as file:
    c = ujson.load(file)

# Settings for the MQTT library
config['client_id']                     = c.get('client_id')
config['server']                        = c.get('server')
config['port']                          = c.get('port')
config['ssid']                          = c.get('ssid')
config['wifi_pw']                       = c.get('wifi_pw')
config['will']                          = f"logs/{c.get('client_id')}", '{"status": "offline"}', True, 1

# Settings for the sensor reading
config['topic']                         = c.get('topic')
config['sensor_type']                   = c.get('sensor_type', 'dht22')
config['rx_pin']                        = c.get('rx_pin', 26)
config['sda_pin']                       = c.get('sda_pin', 23)
config['scl_pin']                       = c.get('scl_pin', 22)
config['ntp_server']                    = c.get('ntp_server', 'time.cloudflare.com')
config['disable_watchdog']              = c.get('disable_watchdog', False)
config['enable_bme280_additional_data'] = c.get('enable_bme280_additional_data', True)

# Settings for GitHub updates
config['github_token']                  = c.get('github_token', None)
config['github_username']               = c.get('github_username', 'VirtualWolf')
config['github_repository']             = c.get('github_repository', 'esp32-sensor-reader-mqtt')
config['github_ref']                    = c.get('github_ref', 'main')

# MQTT topics to subscribe to for receiving commands and emitting logs
config['commands_topic']                = f"commands/{c.get('client_id')}"
config['logs_topic']                    = f"logs/{c.get('client_id')}"

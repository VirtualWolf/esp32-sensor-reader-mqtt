import ujson
from mqtt import config

with open('config.json', 'r') as file:
    c = ujson.load(file)

# Settings for the MQTT library
config['client_id']     = c.get('client_id')
config['server']        = c.get('server')
config['port']          = c.get('port')
config['clean_init']    = c.get('clean_init', True)
config['clean']         = c.get('clean', True)
config['ssid']          = c.get('ssid')
config['wifi_pw']       = c.get('wifi_pw')

# Settings for the sensor reading
config['topic']         = c.get('topic')
config['sensor_type']   = c.get('sensor_type', 'dht22')
config['sda_pin']       = c.get('sda_pin', 23)
config['scl_pin']       = c.get('scl_pin', 22)
config['ntp_server']    = c.get('ntp_server', 'time.cloudflare.com')
config['github_token']  = c.get('github_token', None)
config['signing_secret']    = c.get('signing_secret', None)
config['disable_watchdog']  = c.get('disable_watchdog', False)
config['enable_bme280_additional_data'] = c.get('enable_bme280_additional_data', True)

def read_configuration():
    return config

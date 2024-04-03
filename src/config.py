import ujson
from mqtt import config

with open('config.json', 'r') as file:
    c = ujson.load(file)

config['client_id']     = c.get('client_id')
config['server']        = c.get('server')
config['port']          = c.get('port')
config['clean_init']    = c.get('clean_init', True)
config['clean']         = c.get('clean', True)
config['ssid']          = c.get('ssid')
config['wifi_pw']       = c.get('wifi_pw')
config['ntp_server']    = c.get('ntp_server', 'time.cloudflare.com')
config['sensor_type']   = c.get('sensor_type', 'dht22')
config['github_token']  = c.get('github_token', None)
config['signing_secret'] = c.get('signing_secret', None)

def read_configuration():
    return c

import ujson
from mqtt_as import config

file = open('config.json', 'r')
c = ujson.load(file)
file.close()

config['client_id']     = c.get('client_id')
config['server']        = c.get('server')
config['port']          = c.get('port')
config['clean_init']    = c.get('clean_init', True)
config['clean']         = c.get('clean', True)
config['ssid']          = c.get('ssid')
config['wifi_pw']       = c.get('wifi_pw')
config['ntp_server']    = c.get('ntp_server', 'time.cloudflare.com')

def read_configuration():
    return c

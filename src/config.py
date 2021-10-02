import ujson
from mqtt_as import config
from ubinascii import hexlify

file = open('config.json', 'r')
c = ujson.load(file)
file.close()

config['client_id'] = hexlify(c['client_id'])
config['server'] = c['server']
config['port'] = c['port']
config['clean_init'] = False
config['clean'] =  False
config['ssid'] = c['ssid']
config['wifi_pw'] = c['wifi_pw']

def read_configuration():
    return c

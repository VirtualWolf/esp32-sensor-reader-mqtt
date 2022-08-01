# esp32-sensor-reader-mqtt
A version of my [esp32-sensor-reader](https://github.com/VirtualWolf/esp32-sensor-reader) that reads from an attached AM2303/DHT22 temperature/humidity sensor and publishes the readings as JSON to a local MQTT broker. Uses Peter Hinch's [mqtt_as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md) driver.

Requires a file called `config.json` inside `src` with the following contents:

```json
{
    "client_id": "<client-id>",
    "server": "<broker-address>",
    "port": 1883,
    "topic": "<topic to publish to>",
    "ssid": "<wifi network name>",
    "wifi_pw": "<wifi password>"
}
```

You can optionally add the following to override the default MQTT library values of `true` for `clean` and `clean_init`, and to use your own NTP server instead of `time.cloudflare.com` for time setting on board startup:

```json
    "clean": false,
    "clean_init": false,
    "ntp_server": "10.0.0.1"
```

On an [Adafruit HUZZAH32](https://www.adafruit.com/product/3405), the red LED on the board will light up when it has connectivity to the MQTT broker and will go out when the connectivity stops.

# esp32-sensor-reader-mqtt
A version of my [esp32-sensor-reader](https://github.com/VirtualWolf/esp32-sensor-reader) that reads from an attached AM2303/DHT22 temperature/humidity sensor and publishes the readings as JSON to a local MQTT broker. Uses Peter Hinch's [mqtt_as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md) driver.

Requires a file called `config.json` inside `src` with the following contents:

```
{
    "client_id": "<client-id>",
    "server": "<broker-address>",
    "port": <port to connect to the broker on>,
    "topic": "<topic to publish to>",
    "ssid": "<wifi network name>",
    "wifi_pw": "<wifi password>"
}
```

On an [Adafruit HUZZAH32](https://www.adafruit.com/product/3405), the red LED on the board will light up when it has connectivity to the MQTT broker.

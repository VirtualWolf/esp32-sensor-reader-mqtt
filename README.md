# esp32-sensor-reader-mqtt
A version of my [esp32-sensor-reader](https://github.com/VirtualWolf/esp32-sensor-reader) that reads from an attached AM2303/DHT22 temperature/humidity sensor and publishes the readings as JSON to a local MQTT broker.

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

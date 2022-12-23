# esp32-sensor-reader-mqtt
A version of my [esp32-sensor-reader](https://github.com/VirtualWolf/esp32-sensor-reader) that reads from an attached AM2303/DHT22 temperature/humidity sensor and publishes the readings as JSON to a local MQTT broker. Uses Peter Hinch's [mqtt_as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md) driver.

## Usage

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

## Checking and updating code and configuration remotely
The ESP32 will subscribe to two topics, `commands/<CLIENT_ID>/update` and `commands/<CLIENT_ID>/get_config`.

### Get current config
Sending a message to the `get_config` topic (with any message content, it doesn't matter what it is) will cause the ESP32 to publish a message to `logs/<CLIENT_ID>` with the current `config.json` file, with the wifi password blanked out, so you can double-check how a given board is configured.

### Updating code
Sending a message to the `commands/<CLIENT_ID>/update` topic with the following JSON body...

```json
    {
        "update_code": true
    }
```

...will use [Senko](https://github.com/RangerDigital/senko) to pull down the latest committed code from the primary branch of this repository on GitHub and will restart the ESP32 when finished.

### Updating configuration
Sending a message to the `commands/<CLIENT_ID>/update` topic with the following JSON body...

```json
    {
        "config": {
            "server": "<broker-address>"
        }
    }
```

...will trigger an update of the `config.json` file for the given fields in the `config` object. In the example above, this would update _just_ the `server` value and all the other existing values will be kept. Once the update is finished, the ESP32 will restart.

## Extras

On an [Adafruit HUZZAH32](https://www.adafruit.com/product/3405), the red LED on the board will light up at boot and will turn off once connectivity to wifi and the MQTT broker is established. If the connection drops out, the LED will come back on.

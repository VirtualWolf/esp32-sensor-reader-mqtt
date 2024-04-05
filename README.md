# esp32-sensor-reader-mqtt
A version of my [esp32-sensor-reader](https://github.com/VirtualWolf/esp32-sensor-reader) that reads from an attached DHT22 temperature/humidity sensor or Bosch BME280 temperature/humidity/air pressure sensor and publishes the readings as JSON to a local MQTT broker. Uses Peter Hinch's [mqtt_as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md) MQTT library, as well as Robert Hammelrath's [BME280](https://github.com/robert-hh/BME280/) library if you're using a BME280 instead of a DHT22.

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

If you're using a BME280 sensor instead of a DHT22, you'll need to specify the sensor type as well:

```json
    "sensor_type": "bme280"
```

If you're using several BME280s, you might not care about the atmospheric pressure and dew point data for any that aren't located outside, in which case you can disable it from being sent to the MQTT broker at all:

```json
    "enable_bme280_additional_data": false
```

By default, the board will restart itself automatically if it's not able to either read the sensor or publish to the MQTT topic after two minutes. You can override this by setting the `disable_watchdog` option:

```json
    "disable_watchdog": true
```

## Checking and updating code and configuration remotely
The ESP32 will subscribe to three topics:

* `commands/<CLIENT_ID>/get_config`
* `commands/<CLIENT_ID>/get_system_info`
* `commands/<CLIENT_ID>/update`

### Get current config
Sending a message to the `get_config` topic (with any message content, it doesn't matter what it is) will cause the ESP32 to publish a message to `logs/<CLIENT_ID>` with the current `config.json` file, with the wifi password blanked out, so you can double-check how a given board is configured.

### Get system info
Sending a message to the `get_system_info` topic (with any message content, it doesn't matter what it is) will cause the ESP32 to publish a message to `logs/<CLIENT_ID>` with the MicroPython version of the board and the value of `gc.free_mem()`.

### Updating code
Sending a message to the `commands/<CLIENT_ID>/update` topic with the following JSON body...

```json
    {
        "update_code": true
    }
```

...will pull down the full contents of latest committed code from the `src` directory of the primary branch of this repository on GitHub and will restart the ESP32 when finished.

### Updating configuration
Sending a message to the `commands/<CLIENT_ID>/update_config` topic with the following JSON body...

```json
    {
        "config": {
            "server": "<broker-address>"
        }
    }
```

...will trigger an update of the `config.json` file for the given fields in the `config` object. In the example above, this would update _just_ the `server` value and all the other existing values will be kept. Once the update is finished, the ESP32 will restart.

## Extras

### LED status
On an [Adafruit HUZZAH32](https://www.adafruit.com/product/3405), the red LED on the board will light up at boot and will turn off once connectivity to wifi and the MQTT broker is established. If the connection drops out (either wifi or to the MQTT broker), the LED will come back on. On the [Unexpected Maker FeatherS2](https://feathers2.io), the red power LED always remains on and the blue LED in the middle of the board is used for status instead.

### Ansible runbooks
Also included in this repository are the [Ansible](https://www.ansible.com) runbooks I use to erase and re-flash the ESP with a specified version of MicroPython, to generate the `config.json` file for each board/sensor setup, and to copy the code over to the board. These are particular for my setup so you'll need to adapt them for yourself.

Run them with `ansible-playbook ansible/playbooks/<file>`:

  * `flash_board.yml` — This will erase the board, download MicroPython, and flash it to the board. I have [Adafruit HUZZAH32](https://www.adafruit.com/product/3405) and [Unexpected Maker FeatherS2](https://feathers2.io) devices, but the `vars` dict in the playbook can be updated for other boards.
  * `copy_code_dev.yml` — This will generate the `config.json` file and prompt for a client_id, MQTT broker address, the topic to publish to, and which sensor type you're using.
  * `copy_code_prod.yml` — This is my "production" configuration I use for the temperature sensors that are set up permanently around the house. It only prompts for the client_id and sensor type and the rest is hard-coded to avoid me making any configuration mistakes if I need to reflash the board.

### Adding a self-contained Ansible installation
* Install and configure [pyenv](https://github.com/pyenv/pyenv)
* Install the version of Python for this project — `pyenv install`
* Add a new virtualenv for this project — `python -m venv .venv`
* Activate the virtualenv — `. .venv/bin/activate`
* Install Ansible — `pip install -r dev-requirements.txt`

Before running any `ansible-playbook` commands, load the virtualenv with `. .venv/bin/activate`.

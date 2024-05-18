# Overview
A version of my [esp32-sensor-reader](https://github.com/VirtualWolf/esp32-sensor-reader) combined with [esp32-air-quality-reader-mqtt](https://github.com/VirtualWolf/esp32-air-quality-reader-mqtt) that reads from an attached DHT22 temperature/humidity sensor, Bosch BME280 temperature/humidity/air pressure sensor, Plantower PMS5003 air quality sensor, or ScioSense ENS160 air quality sensor, and publishes the readings as JSON to a local MQTT broker.

Libraries used:
* Peter Hinch's [mqtt_as.py](https://github.com/peterhinch/micropython-mqtt/blob/master/mqtt_as/README.md) MQTT library
* Robert Hammelrath's [BME280](https://github.com/robert-hh/BME280/) library if you're using a BME280 instead of a DHT22
* glenn20's [micropython-esp32-ota](https://github.com/glenn20/micropython-esp32-ota/) for over-the-air firmware updates
* Jakub Bednarski's [senko](https://github.com/RangerDigital/senko/) as the original basis from the [update_from_github.py](src/update_from_github.py) code
* Christopher Arndt's [mrequests](https://github.com/SpotlightKid/mrequests) for ease of streaming files from GitHub to flash to avoid the memory issues of regular `requests`
* [My fork](https://github.com/VirtualWolf/ENS160) of Lukasz Awsiukiewicz's [ENS160](https://github.com/awsiuk/ENS160) library

# Configuration

Requires a file called `config.json` inside `src` with the following contents:

```json
{
    "client_id": "<client-id>",
    "server": "<broker-address>",
    "port": 1883,
    "ssid": "<wifi network name>",
    "wifi_pw": "<wifi password>",
    "sensors": [...]
}
```

The `sensors` array needs to be filled out as described below depending on which type of sensor(s) you have attached to the ESP32.

Once configured, copy the whole contents of the `src` directory to the board with [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html) and restart it when it's finished:

```
$ cd src
$ mpremote connect port:/dev/tty.SLAB_USBtoUART cp -r . : + reset"
```

(Substituting `/dev/tty.SLAB_USBtoUART` for your specific board's serial port.)

Alternatively you can adapt the [Ansible runbooks described below](#ansible-runbooks) for your own use.

## DHT22 temperature/humidity sensor

For a DHT22 sensor, you'll need set the sensor type, the data pin it's attached to, and the topic to publish the data to:

```json
    "sensors": [
        {
            "type": "dht22",
            "rx_pin": 26,
            "topic": "home/outdoor/weather"
        }
    ]
```

## BME280 temperature/humidity/air pressure sensor

For a BME280, you'll need to specify the sensor type, the I2C address of the sensor, and topic to publish to. You can also explicitly set the I2C SDA and SCL pins if needed (these default to 23 and 22 respectively if not specified):

```json
    "sensors": [
        {
            "type": "bme280",
            "i2c_address": 119,
            "topic": "home/outdoor/weather"
        }
    ],
    "sda_pin": 19,
    "scl_pin": 18
```

If you're using several ESP32s with BME280s, you might not care about the atmospheric pressure and dew point data for any that aren't located outside, in which case you can disable those datapoints from being sent to the MQTT broker by setting `enable_addtional_data` to `false`:

```json
    "sensors": [
        {
            "type": "bme280",
            "i2c_address": 119,
            "topic": "home/indoor/weather",
            "enable_addtional_data": false
        }
    ],
```

## PMS5003 air quality sensor

For a PMS5003 sensor, you'll need set the sensor type, the data pin it's attached to, and the topic to publish the data to:

```json
    "sensors": [
        {
            "type": "pms5003",
            "rx_pin": 26,
            "topic": "home/outdoor/airquality"
        }
    ]
```
## ENS160 air quality sensor

If you're using a ENS160 sensor, you'll need to specify the sensor type, I2C address of the sensor, and topic to publish to. You can also explicitly set the I2C SDA and SCL pins if needed (these default to 23 and 22 respectively if not specified):

```json
    "sensors": [
        {
            "type": "ens160",
            "i2c_address": 83,
            "topic": "home/indoor/airquality"
        }
    ],
    "sda_pin": 19,
    "scl_pin": 18
```

The ENS160 has built-in calibration based on temperature and humidity readings, if you're using it by itself it will always use values of 25˚C and 50% relative humidity but you have a DHT22 or BME280 attached as well, it will calibrate itself based on the values read from that sensor.

## Using multiple sensors

If you have multiple sensor attached to a single board, you can add additional objects to the `sensors` array:

```json
    "sensors": [
        {
            "type": "bme280",
            "i2c_address": 119,
            "topic": "home/indoor/weather"
        },
        {
            "type": "ens160",
            "i2c_address": 83,
            "topic": "home/indoor/airquality"
        }
    ],
    "sda_pin": 19,
    "scl_pin": 18
```

## Other options

You can use your own NTP server instead of `time.cloudflare.com` for time setting on board startup:

```json
    "ntp_server": "10.0.0.1"
```

By default, the board will restart itself automatically if it's not able to either read the sensor or publish to the MQTT topic after a period of time (ten minutes for the PMS5003, two minutes for any other sensor). You can override this by setting the `disable_watchdog` option:

```json
    "disable_watchdog": true
```

By default the remote code updating described below will default to the `main` branch of this repository (`https://github.com/VirtualWolf/esp32-sensor-reader-mqtt`) but those settings can be customised with the following options:

```json
    "github_token": "a-very-secret-token",
    "github_username": "jdoe",
    "github_repository": "my-esp32-sensor-reader-fork",
    "github_ref": "a-branch-or-tag-or-commit"
```

The `github_token` variable is only required if the repository is private.

# MQTT data

The data that's sent to MQTT will vary depending on the sensor type being used.

For a DHT22 (or a BME280 with `enable_bme280_additional_data` set to `false`):

```json
{
    "timestamp": <epoch time in milliseconds>,
    "temperature": <number>,
    "humidity": <number>
}
```

For a BME280 with `enable_bme280_additional_data` set to `true` (or not explicitly specified):

```json
{
    "timestamp": <epoch time in milliseconds>,
    "temperature": <number>,
    "humidity": <number>,
    "dew_point": <number>,
    "pressure": <number>
}
```

For a PMS5003:

```json
{
    "timestamp": <epoch time in milliseconds>,
    "pm_1_0": <number>,
    "pm_2_5": <number>,
    "pm_10": <number>,
    "particles_0_3um": <number>,
    "particles_0_5um": <number>,
    "particles_1_0um": <number>,
    "particles_2_5um": <number>,
    "particles_5_0um": <number>,
    "particles_10um": <number>
}
```

For an ENS160:

```json
{
    "timestamp": <epoch time in milliseconds>,
    "aqi": <number>,
    "tvoc": <number>,
    "eco2": <number>
}
```

# Checking and updating configuration, code, and firmware remotely
The ESP32 will subscribe to the topic `commands/<CLIENT_ID>` to listen for commands, and will publish log messages to `logs/<CLIENT_ID>`.

For ease of management, an admin UI lives in the [pi-home-dashboard](https://github.com/VirtualWolf/pi-home-dashboard) repository at `/admin.html`.

## Get current config
Send a message to the `commands/<CLIENT_ID>` topic with the following payload:

```json
{
    "command": "get_config"
}
```

And the current contents of `config.json` will be published to `logs/<CLIENT_ID>` so you can see how a given board is configured.


## Get system info
Send a message to the `commands/<CLIENT_ID>` topic with the following payload:

```json
{
    "command": "get_system_info"
}
```

And a message will be published to to `logs/<CLIENT_ID>` with the current Git commit hash, the MicroPython version of the board, and the value of `gc.free_mem()`.

## Updating configuration
Send a message to the `commands/<CLIENT_ID>` topic with the following payload:

```json
{
    "command": "update_config",
    "config": {
        "server": "<broker-address>"
    }
}
```

And the board will trigger an update of the `config.json` file for the given fields in the `config` object. In the example above, this would update _just_ the `server` value and all the other existing values will be kept. Once the update is finished, the ESP32 will restart.

To _remove_ a configuration option, send the configuration option with an empty string:

```json
{
    "command": "update_config",
    "config": {
        "ntp_server": ""
    }
}
```

Note that the _required_ options (`client_id`, `server`, `port`, `ssid`, and `wifi_pw`) cannot be deleted, only updated to new values.

## Replacing configuration
To replace the entire configuration of the board all in one go, send a message to the `commands/<CLIENT_ID>` topic with the following payload:

```json
{
    "command": "replace_config",
    "config": {
        "ssid": "<wifi network name>",
        "wifi_pw": "<wifi password>",
        "server": "<broker-address>",
        "port": 1883,
        "client_id": "<client-id>",
        [...]
    }
}
```

The replacement configuration will be rejected if the minimum required keys listed in `config` above aren't set.

## Restarting the board
Send a message to the `commands/<CLIENT_ID>` topic with the following payload:

```json
{
    "command": "restart"
}
```

And the board will run a `machine.reset()` and restart itself.

## Updating code
Send a message to the `commands/<CLIENT_ID>` topic with the following payload:

```json
{
    "command": "update_code"
}
```

And it pull down the full contents of latest committed code from the `src` directory of the primary branch of this repository on GitHub and will restart the ESP32 when finished. As mentioned above, the location of the code to download can be changed with the `github_username`, `github_repository`, and `github_ref` configuration options.

## Updating firmware
If the version of MicroPython running on the board supports over-the-air updates (meaning it's been flashed with the "Support for OTA" firmware from the [MicroPython download page](https://micropython.org/download/) for your specific board), you can remote update the version of MicroPython itself.

Send a message to the `commands/<CLIENT_ID` topic with the following payload:

```json
{
    "command": "update_firmware",
    "firmware": {
        "url": "https://micropython.org/resources/firmware/ESP32_GENERIC-OTA-20240222-v1.22.2.app-bin",
        "size": <size of firmware file in bytes>,
        "sha256": <SHA256 hash of firmware file>
    }
}
```

And the board will download the given firmware file and update it, verify it, then restart. Upon successful restart the automatic rollback will be cancelled, but if the board doesn't come up correctly it'll revert to the previous version on next hard reset.

For the filename, note the `-OTA-` in the middle indicating it's an OTA-enabled firmware file, and the `.app-bin` extension indicating it's _just_ the MicroPython app image and doesn't include the bootloader or partition table.

For easier updating, use the `/admin.html` page in my [pi-home-dashboard](https://github.com/VirtualWolf/pi-home-dashboard) repository which will calculate the filesize and SHA256 hash, as well as downloading the firmware file locally to use instead of needing to download it afresh from `micropython.org` for every board update you're running.

# Extras

## LED status
On an [Adafruit HUZZAH32](https://www.adafruit.com/product/3405), the red LED on the board will light up at boot and will turn off once connectivity to wifi and the MQTT broker is established. If the connection drops out (either wifi or to the MQTT broker), the LED will come back on. On the [Unexpected Maker FeatherS2](https://feathers2.io), the red power LED always remains on and the blue LED in the middle of the board is used for status instead.

## Ansible runbooks
Also included in this repository are the [Ansible](https://www.ansible.com) runbooks I use to erase and re-flash the ESP with a specified version of MicroPython, to generate the `config.json` file for each board/sensor setup, and to copy the code over to the board. These are particular for my setup so you'll need to adapt them for yourself.

Run them with `ansible-playbook ansible/playbooks/<file>`:

  * `flash_board.yml` — This will erase the board, download MicroPython, and flash it to the board. I have [Adafruit HUZZAH32](https://www.adafruit.com/product/3405), [Adafruit QT Py ESP32-Pico](https://www.adafruit.com/product/5395), and [Unexpected Maker FeatherS2](https://feathers2.io) devices, but the inventory can be updated for other boards.
  * `copy_code_dev.yml` — This will prompt for the board type, sensor configuration, and client_id, and will generate the `config.json` file and copy the files to the board then restart it.
  * `copy_code_prod.yml` — This is my "production" configuration I use for the temperature sensors that are set up permanently around the house. It only prompts for the client_id and the rest is either calculated based on that or is hard-coded, to avoid me making any configuration mistakes if I need to reflash the board.

## Adding a self-contained Ansible installation
* Install and configure [pyenv](https://github.com/pyenv/pyenv)
* Install the version of Python for this project — `pyenv install`
* Add a new virtualenv for this project — `python -m venv .venv`
* Activate the virtualenv — `. .venv/bin/activate`
* Install Ansible — `pip install -r dev-requirements.txt`

Before running any `ansible-playbook` commands, load the virtualenv with `. .venv/bin/activate`.

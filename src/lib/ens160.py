# This code is primarily Lukasz Awsiukiewicz's original library at https://github.com/awsiuk/ENS160/
# Minor changes have been made to allow selection of I2C pins and sensor address, and the optional
# ability to feed in temperature and humidity values for calibration rather than defaulting to 25˚C
# and 50% humidity.
#
# Sensor datasheet can be found at https://www.sciosense.com/wp-content/uploads/2023/12/ENS160-Datasheet.pdf

import time

## ENS160 chip version
ENS160PART_ID = 0x160

# ENS160 register addresses
ENS160PART_ID_REG      = 0x00 # This 2-byte register contains the part number in little endian of the ENS160.
ENS160OPMODE_REG       = 0x10 # This 1-byte register sets the Operating Mode of the ENS160.
ENS160CONFIG_REG       = 0x11 # This 1-byte register configures the action of the INTn pin.
ENS160COMMAND_REG      = 0x12 # This 1-byte register allows some additional commands to be executed on the ENS160.
ENS160TEMP_IN_REG      = 0x13 # This 2-byte register allows the host system to write ambient temperature data to ENS160 for compensation.
ENS160RH_IN_REG        = 0x15 # This 2-byte register allows the host system to write relative humidity data to ENS160 for compensation.
ENS160DATA_STATUS_REG  = 0x20 # This 1-byte register indicates the current STATUS of the ENS160.
ENS160DATA_AQI_REG     = 0x21 # This 1-byte register reports the calculated Air Quality Index according to the UBA.
ENS160DATA_TVOC_REG    = 0x22 # This 2-byte register reports the calculated TVOC concentration in ppb.
ENS160DATA_ECO2_REG    = 0x24 # This 2-byte register reports the calculated equivalent CO2-concentration in ppm, based on the detected VOCs and hydrogen.
ENS160DATA_ETOH_REG    = 0x22 # This 2-byte register reports the calculated ethanol concentration in ppb.
ENS160DATA_T_REG       = 0x30 # This 2-byte register reports the temperature used in its calculations (taken from TEMP_IN, if supplied).
ENS160DATA_RH_REG      = 0x32 # This 2-byte register reports the relative humidity used in its calculations (taken from RH_IN if supplied).
ENS160DATA_MISR_REG    = 0x38 # This 1-byte register reports the calculated checksum of the previous DATA_ read transaction (of n-bytes).
ENS160GPR_WRITE_REG    = 0x40 # This 8-byte register is used by several functions for the Host System to pass data to the ENS160.
ENS160GPR_READ_REG     = 0x48 # This 8-byte register is used by several functions for the ENS160 to pass data to the Host System.

# OPMODE (Address 0x10) register modes
ENS160SLEEP_MODE       = 0x00 # DEEP SLEEP mode (low power standby)
ENS160IDLE_MODE        = 0x01 # IDLE mode (low-power)
ENS160STANDARD_MODE    = 0x02 # STANDARD gas sensing modes.

# CMD(0x12) register commands
ENS160COMMAND_NOP          = 0x00 # Reserved, no command
ENS160COMMAND_GET_APPVER   = 0x0E # Get Firmware Version command
ENS160COMMAND_CLRGPR       = 0xCC # Clear GPR Read Registers command

class ENS160:
    def __init__(self, i2c, address=0x53, temperature=25, humidity=50):
        self.ENS160ADDR = address
        self.temperature = temperature
        self.humidity = humidity

        try:
            self.i2c = i2c

            buf = bytearray(1)
            buf[0] = ENS160STANDARD_MODE

            self.i2c.writeto_mem(self.ENS160ADDR, ENS160OPMODE_REG, buf)

            time.sleep(0.025)

            self.calibrate_temperature(self.temperature)
            self.calibrate_humidity(self.humidity)
        except OSError:
            print('Failed to initialise: ', OSError)

    def calibrate_temperature(self, temperature):
        # Calculations based on chip documentation on page 29
        temperature = (temperature + 273.15) * 64

        # Array that will hold data of temperature
        buf = bytearray(2)

        # Low byte of temperature
        buf[0] = temperature and 0xFF
        # High byte of temperature
        buf[1] = (temperature and 0xFF00) >> 8

        self.i2c.writeto_mem(self.ENS160ADDR, ENS160TEMP_IN_REG, buf)

        time.sleep(0.025)

    def calibrate_humidity(self, humidity):
        # Calculation based on chip documentation on page 29
        humidity = humidity*512

        buf = bytearray(2)
        buf[0] = humidity and 0xFF
        buf[1] = (humidity and 0xFF00) >> 8

        self.i2c.writeto_mem(self.ENS160ADDR, ENS160RH_IN_REG, buf)

        time.sleep(0.025)

    def get_readings(self):
        aqi = self.i2c.readfrom_mem(self.ENS160ADDR, ENS160DATA_AQI_REG, 1)
        tvoc = self.i2c.readfrom_mem(self.ENS160ADDR, ENS160DATA_TVOC_REG, 2)
        eco2 = self.i2c.readfrom_mem(self.ENS160ADDR, ENS160DATA_ECO2_REG, 2)

        return (aqi[0], (tvoc[1]<<8 | tvoc[0]), (eco2[1]<<8 | eco2[0]))

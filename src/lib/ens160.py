import time

# Datasheet can be found at https://www.sciosense.com/wp-content/uploads/2023/12/ENS160-Datasheet.pdf

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

            time.sleep(0.2)

            self.calibrate_temperature(self.temperature)
            self.calibrate_humidity(self.humidity)
        except OSError:
            print('failed to init, Assigned the correct pins on machine.Pin() if you get [Errno 19] ENODEV ')

    def calibrate_temperature(self, temperature):
        #doing calculations based on chip documentation on page 27
        #not yet sure if this should be float as argument to function is int - to be tested
        temperature = (temperature + 273.15) * 64
        #building array that will hold data of _temp
        buf = bytearray(2)
        #grabing low byte
        buf[0] = temperature and 0xFF
        #grabing high byte of _temp
        buf[1] = (temperature and 0xFF00) >> 8

        self.i2c.writeto_mem(self.ENS160ADDR, ENS160TEMP_IN_REG, buf)

        time.sleep(0.2)

    def calibrate_humidity(self, humidity):
        #doing calculations based on chip documentation on page 27
        humidity = humidity*512

        buf = bytearray(2)
        buf[0] = humidity and 0xFF
        buf[1] = (humidity and 0xFF00) >> 8

        self.i2c.writeto_mem(self.ENS160ADDR, ENS160RH_IN_REG, buf)
        time.sleep(0.2)

    def getAQI(self):
        buf = self.i2c.readfrom_mem(self.ENS160ADDR, ENS160DATA_AQI_REG, 1)

        return (buf[0])

    def getTVOC(self):
        buf = self.i2c.readfrom_mem(self.ENS160ADDR, ENS160DATA_TVOC_REG, 2)

        return (buf[1]<<8 | buf[0])

    def getECO2(self):
        buf = self.i2c.readfrom_mem(self.ENS160ADDR, ENS160DATA_ECO2_REG, 2)

        return (buf[1]<<8 | buf[0])

    def get_readings(self):
        aqi = self.getAQI()
        tvoc = self.getTVOC()
        eco2 = self.getECO2()

        return (aqi, tvoc, eco2)

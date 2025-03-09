# This is a very lightly modfied version of the original code from Core Electronics:
# https://github.com/CoreElectronics/CE-PiicoDev-RGB-LED-MicroPython-Module
# It's been changed to remove the dependency on the Piico Unified Library and to use
# a full passed-in I2C object the same as the other libraries in this repository.

from time import sleep_ms

_baseAddr=0x08
_DevID=0x84
_regDevID=0x00
_regFirmVer=0x01
_regCtrl=0x03
_regClear=0x04
_regI2cAddr=0x05
_regBright=0x06
_regLedVals=0x07

class PiicoDev_RGB(object):
    def setPixel(self,n,c):
        self.led[n]=[round(c[0]),round(c[1]),round(c[2])]

    def show(self):
        buffer = bytes(self.led[0]) + bytes(self.led[1]) + bytes(self.led[2])
        self.i2c.writeto_mem(self.addr, _regLedVals, buffer)

    def setBrightness(self,x):
        self.bright= round(x) if 0 <= x <= 255 else 255
        self.i2c.writeto_mem(self.addr, _regBright, bytes([self.bright]))
        sleep_ms(1)

    def clear(self):
        self.i2c.writeto_mem(self.addr,_regClear,b'\x01')
        self.led=[[0,0,0],[0,0,0],[0,0,0]]
        sleep_ms(1)

    def setI2Caddr(self, newAddr):
        x=int(newAddr)
        assert 8 <= x <= 0x77, 'address must be >=0x08 and <=0x77'
        self.i2c.writeto_mem(self.addr, _regI2cAddr, bytes([x]))
        self.addr = x
        sleep_ms(5)

    def readFirmware(self):
        v=self.i2c.readfrom_mem(self.addr, _regFirmVer, 2)
        return (v[1],v[0])

    def readID(self):
        return self.i2c.readfrom_mem(self.addr, _regDevID, 1)[0]

    # Control the 'Power' LED. Defaults ON if anything else but False is passed in
    def pwrLED(self, state):
        assert state == True or state == False, 'argument must be True/1 or False/0'
        self.i2c.writeto_mem(self.addr,_regCtrl,bytes([state]))
        sleep_ms(1)

    def fill(self,c):
        for i in range(len(self.led)):
            self.led[i]=c
        self.show()

    def __init__(self, i2c, address=_baseAddr, bright=50):
        self.i2c = i2c
        self.addr = address
        self.led = [[0,0,0],[0,0,0],[0,0,0]]
        self.bright=bright
        try:
            self.setBrightness(bright)
            self.show()
        except Exception as e:
            print("* Couldn't find a device - check switches and wiring")
            raise e

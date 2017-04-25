# Communication between RPI and Arduino, using I2C
# Goal:
#	RPI should be able to receive data from Arduino, and send data to Arduinoto adjust
#	parameters. The reason for using I2C instead of other methods:
#		1. Serial port monitor prevents us from implementing our GUI
#		2. Serial communication ports are take up for Arduino to talk with the furnaces built-in temperature controller

import smbus
import time

bus = smbus.SMBus(1)    # RPI: 0 = /dev/i2c-0 (port I2C0), 1 = /dev/i2c-1 (port I2C1)

# Initialization
addr = 0x04      #7 bit address (will be left shifted to add the read write bit)
some_reg = ''
data = ''

# Convert command string to command bytes for the Arduino
def StringToBytes(data):
	retVal = []
	for c in data:
		retVal.append(ord(c))
	return retVal

# Retrieve bus status of Arduino
def getStatus(addr):
        status = ""
        for i in range (0, 64):
            status += chr(bus.read_byte(addr))
        time.sleep(0.01)        
        return status

# Send a command to the Arduino from RPI
def communication_send(addr, some_reg, data):
	data = StringToBytes(data)
	some_reg = ord(some_reg[0].upper())
	print "stuck"
	bus.write_i2c_block_data(addr, some_reg, data)
	print "unstuck"
	time.sleep(0.2)

# Receive status to the RPI from Arduino
def communication_receive(addr):
	status = getStatus(addr)
	return status

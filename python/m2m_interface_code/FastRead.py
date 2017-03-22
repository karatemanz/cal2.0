# fast reading data
# USED to read temperature data from the infrared sensors or thermocouple
# PROTOCOL: SPI
# CHIPS: MCP3008(10-bit Analog to Digital Converter)
#   	 MCP3208(12-bit Analog to Digital Converter)

import numpy as np
import matplotlib.pyplot as plt
import spidev
import time
import os
import RPi.GPIO as GPIO
from pylab import *

solenoid_valve_pin = 13
GPIO.setup(solenoid_valve_pin, GPIO.OUT)
GPIO.output(solenoid_valve_pin, GPIO.LOW)

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)

# Define sensor channel
adt = 0
adt2 = 3
counter = 0

Vref = 4.96*(653.7/330.0) # Vref is the voltage applied on ADC
Vref2 = 4.96
#A1Temp = 690
#TMP36 = 1

# Functions to read SPI data from temperature sensors
# ----------------------------------------------------------------------------

# 10-bit READ data from MCP3008(10 bit adc) chip
def ReadChannel_10bit(channel):
	adc = spi.xfer2([1,(8+channel)<<4,0])
	data = ((adc[1]&3) << 8) + adc[2]
	return data

# 12-bit READ data from MCP3208 chip
# Approach => oversampling and then averaging the result to reduce noise
def ReadChannel_12bit(channel):

	rate = 0

	# averaging 8 readings
	for i in range (0,8):
		adc = spi.xfer2([6 | (channel >> 2), (channel & 3) << 6, 0])
		data = ((adc[1] & 15)<< 8) + adc[2]
		rate += data
		#time.sleep(0.000001)

	data = rate/8.0
	return data

# Functions to convert data to voltage level,
# Rounded to specified number of decimal places based on the bit precision
#---------------------------------------------------------------------------

# 10-bit CONVERT to volts from the data provided with 10 bits of precision
# Data Source => When using MCP3008(10 bit adc)
def ConvertVolts_10bit(data, places):
	volts = (data*Vref)/float(1024)
	volts = round(volts, places)
	return volts

# 12-bit CONVERT to volts from the data provided with 12-bits of precision
# Data Source => When using MCP3208(12 bit adc)
def ConvertVolts_12bit(data, places):
	volts = (data*Vref)/float(4096)
	volts = round(volts, places)
	return volts

# Function to calculate temperature from TMP36
# Rounded to specified number of decimal places.
"""
def ConvertTemp_TMP36(data, places):

	temp = ((data*330)/float(1023))-45
	temp = round(temp, places)
	return temp
"""

# Define delay between readings
#delay = 0.00001
# Define the length of the test
#length = 10.0
# Create two lists to store the temperature data and corresponding time
#i = 0

# READ from

def fastRead(frequency, temp, A1Temp, ADT):
	#delay between readings based on frequency
	delay = 1.0/frequency
	valvelock = 0
	# Create two lists to store the temperature data and corresponding time
	"""
	# If we are using IR SENSOR PSC-T42L, whose measurement
	# range is -40C to 1000C. Its output current is 4 to 20mA, 
	# by mapping temp to current we get their relationship:
	current  = ((1.0/65.0)*temp + (60.0/13.0))/1000.0
	# when using 3.3v Vref, load resister = 3.3/0.02 = 165
	target_volt = 165*(current)
	
	# We are using IR Sensor Sirius SI23, whose measurement
	# range is 150C to 900C. Its output current is 4 to 20mA,
	# mapping temp to current, we get their relationship:
	current = ((8.0/375)*temp + (0.8))/1000.0 
	# when using 3.3v Vref, load resister = 3.3/0.02 = 165
	target_volt = 165.0*(current)
	# when using MCP3008(10 bit adc)
	#threshold = (target_volt*1023)/3.3

	# when using MCP3208(12 bit adc)
	threshold = (target_volt*4095)/3.3
	temp_level=[]
	time_elapsed = []
	StartTime = time.time()
	while (ReadChannel(ADT) > threshold):
	#for i in range (0, 1000):
		# read from sensor	
		temp_level.append(ReadChannel_12bit(ADT))
		time_elapsed.append(time.time() - StartTime)
		time.sleep(delay)
	return time_elapsed,temp_level
	"""
	temp_level=[]
	time_elapsed = []
	StartTime = time.time()

	if ADT == 0 :
		Threshold = (temp*0.005 + 1.25)*4096.0/Vref
	if ADT == 3:
		Threshold = ((temp+12.5)/402.70531)*4096.0/Vref2
		Threshold2 = ((A1Temp+12.5)/402.70531)*4096.0/Vref2

	print temp, Threshold
	counter = 0

 	while counter < 3:
	#for i in range (0, 30):
		# read from sensor
		temp_level.append(ReadChannel_12bit(ADT))
		time_elapsed.append(time.time() - StartTime)
		time.sleep(delay)

		if (ReadChannel_12bit(ADT) < Threshold2) and valvelock == 0:
			GPIO.output(solenoid_valve_pin, GPIO.HIGH)
			valvelock = 1
		if (ReadChannel_12bit(ADT) < Threshold):
			counter += 1

	return time_elapsed, temp_level


# NOT USED AS FAR AS I CAN TELL
def fastRead2():

	temp_level=[]
	time_elapsed = []
	StartTime = time.time()
	delay = 0.1

	for i in range (0, 30):
		# read from sensor	
		temp_level.append(ReadChannel_12bit(adt))
		time_elapsed.append(time.time() - StartTime)
		time.sleep(delay)

	return time_elapsed,temp_level
	#spi.close()
	# print "Delay Time = %r"%delay
	# print "Actual sample points recored in 10 seconds: %r"%(len(temp_level))

"""
time,temp = fastRead2()
RoundTime  = [round(elem, 4) for elem in time]
ADT_VOLT = [(elem*Vref)/float(4096) for elem in temp]

# Voltage divider, R1+R2 = 19.395kohm, R2=9.74khom, Y = (R1+R2)/R2 = 1.9892
# Using thermocouple
ADT_TEMP = [round((elem-1.25)/0.005,2) for elem in ADT_VOLT]
# Using IR sensor
#ADT_TEMP = [round((422.705314*elem-6.25)/(653.7/330.0),2) for elem in ADT_VOLT]

x = np.array(RoundTime)
y = np.array(ADT_TEMP)
plt.plot(x,y)
#plt.ylim(0,40)
xlabel('time (s)')
ylabel('Temp (C)')
title('Test thermocouple')
grid(True)
show()
print len(ADT_TEMP)
"""





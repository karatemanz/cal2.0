# Code of the solenoid control, in cooperation with the adc mcp3008 which is used for reading the
# potentiometer.

# TODO: Gate Control Code -> Read the Potentiometer To Move The Gate Based On Sample Position

# Important:
# ***The potentiometer sensitivity is 0.0014 V/mm***

import spidev
import RPi.GPIO as GPIO
import time

Vref = 4.96
spi = spidev.SpiDev()
spi.open(0,0)

sample_len = 0.18    # 7 inch sample
#sample_len = 0.18   # half of 280mm/6in, measured between the holder's edge
#sample_len = 0.16   # 3 inch sample
#sample_len = 0.1484 # using 85mm sample, Louis' sample A
#sample_len = 0.138  # Louis' sample B
#sample_len = 0.14

# define hte potentiometer channel on MCP3008
poten_channel = 1

# pin definition for the solenoids
Solenoid_Pin_1 = 26
#Solenoid_Pin_2 = 21
Solenoid_Pin_3 = 21

# Use read_mcp3208.py to find out the voltage
# position definition of gates

Gate_1_pos = 2.045  # Unit: Voltage for 280mm sample
#Gate_1_pos = 1.88  # Unit: Voltage for 85mm sample
#Gate_1_pos = 1.918 # Unit: Voltage for 3 inch sample or 76mm sample
#Gate_1_pos = 2.06

#Gate_2_pos = 2.0

Gate_3_pos = 3.14
#Gate_3_pos = 3.03

# define a safety clearance before the sample hits the gate
safety_clearance = 0.015

# setup solenoid pins 
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(Solenoid_Pin_1, GPIO.OUT)
GPIO.setup(Solenoid_Pin_3, GPIO.OUT)
#GPIO.setup(Solenoid_Pin_2, GPIO.OUT)

# Initial state for LEDs:
GPIO.output(Solenoid_Pin_1, GPIO.LOW)
GPIO.output(Solenoid_Pin_3, GPIO.LOW)
#GPIO.output(Solenoid_Pin_2, GPIO.LOW)

# Read from 12-bits (MCP3208)
# oversampling then averaging the result to reduce noise
def ReadChannel_12bit(channel):

	rate = 0

	for i in range (0,8): # averaging 8 readings
		adc = spi.xfer2([6 | (channel >> 2), (channel & 3) << 6, 0])
		data = ((adc[1] & 15)<< 8) + adc[2]
		rate += data
		#time.sleep(0.0001)
	data = rate/8.0
	return data

# CONVERSION from 10-bit (MCP3008) to 12-bit (MCP3208) precicion values
def ConvertVolts_12bit(data, places):
	# When using MCP3208(12 bit adc)
	volts = (data*Vref)/float(4096)
	volts = round(volts, places)
	return volts

# READ the potentiometer and convert it in to distance
def read_poten(channel):
	data = ReadChannel_12bit(channel)  # ReadChannel is defined in FastRead.py, assume thermocouple is on channel 0
	volt = ConvertVolts_12bit(data, 2) # use volt above to calculate the position of the sample
	sample_pos = volt
	return sample_pos

##################################################

# READ sample position from potentiometer
sample_position = [read_poten(poten_channel)]
sample_position.append(None)

###################################################
# Defined here because definition relies on method read_poten()

# GATE control logic
def gate_control(direction, sample_position, Gate_pos, Solenoid_Pin):

	# DETERMINES safety celearence of sample based on gate position
	if Gate_pos == Gate_3_pos:
		up_safety_clearance = safety_clearance*2
	else:
		up_safety_clearance = safety_clearance*5

    # DETERMINE gate response based on the direction the sample is moving (0 = upward, 1 = downward)
	if direction == 1 and sample_position - Gate_pos < 0:
		if GPIO.input(Solenoid_Pin) == 0 and \
		sample_position + sample_len > Gate_pos - up_safety_clearance:
			GPIO.output(Solenoid_Pin, GPIO.HIGH)
			print "open gate %r" %Solenoid_Pin
			print "judgement 1"
			time.sleep(1.0) #once the state of solenoid changes,hold it for 0.5 sec to prevent unstable bounces
	elif direction == 1 and sample_position - Gate_pos > 0:
		if GPIO.input(Solenoid_Pin) == 1 and \
		sample_position > Gate_pos + 0.3*safety_clearance + sample_len:
			GPIO.output(Solenoid_Pin, GPIO.LOW)
			print "close gate %r" %Solenoid_Pin
			print "judgement 2"
			time.sleep(0.5) #once the state of solenoid changes,hold it for 0.5 sec to prevent unstable bounces
	elif direction == 0 and sample_position - Gate_pos > 0:
		if GPIO.input(Solenoid_Pin) == 0 and \
		sample_position < Gate_pos + 3*safety_clearance + sample_len:
			GPIO.output(Solenoid_Pin, GPIO.HIGH)
			print "open gate %r" %Solenoid_Pin
			print "judgement 3"
			time.sleep(1.0) #once the state of solenoid changes,hold it for 0.5 sec to prevent unstable bounces
	elif direction == 0 and sample_position - Gate_pos < 0:
		if GPIO.input(Solenoid_Pin) == 1 and \
		sample_position < Gate_pos - safety_clearance - sample_len:
			GPIO.output(Solenoid_Pin, GPIO.LOW)
			print "close gate %r" %Solenoid_Pin
			print "judgement 4"
			time.sleep(0.5) #once the state of solenoid changes,hold it for 0.5 sec to prevent unstable bounces

# GATE Control thread
def solenoid_thread():
	# start a thread in main()
	while True:
		direction = 3 # indicator of the sample moving direction
		sample_position[1] = read_poten(poten_channel)
		if sample_position[1] - sample_position[0] > 0:
			direction = 1 # this means sample is moving upward
		elif sample_position[0] - sample_position[1] > 0:
			direction = 0 # this means sample is moving downward

		#  CONTROL the gate based on the direction the sample is moving
		gate_control(direction, sample_position[1], Gate_1_pos, Solenoid_Pin_1)
		#gate_control(direction, sample_position[2], Gate_2_pos, Solenoid_Pin_2)
		#gate_control(direction, sample_position[1], Gate_3_pos, Solenoid_Pin_3)
		sample_position[0] = sample_position[1] 
		time.sleep(0.01)
	#finally:
		#lock.release()
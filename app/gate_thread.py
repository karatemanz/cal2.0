# Code of the solenoid gate control and mcp3208 Analog-To-Digital Converter which is used for reading the potentiometer
#
# Use:
# 1) Gate driver and testing functions
# 2) Potentiometer reader and tester (Read movement of sample on strip)
# 3) [MAIN] Control gate operation based on stage and movement of sample on strip
#
# Important:
# 1) The protentiometer sensitivity is 0.0014 V/mm
# 2) Reading the channel senses a change in voltages measureing the velocity of the sample movement
# 3) Potentiometer is on channel 1 of the mcp3208 (12-bit ADC)
# 4) Gate 1 (Between Furnace 2 and Cooling Area) is connected to RPI.GPIO pin: 26
# 5) Gate 2 (Between Furnace 1 and Top) is connnected to RPI.GPIO pin: 21

import spidev
import RPi.GPIO as GPIO
import time
import STM
import util as util

Vref = 4.96
spi = spidev.SpiDev()
spi.open(0,0)

# Define potentiometer channel on MCP3208
potenChannel = 1     # Connected to Vref = 4.96

# pin definition for the solenoids
solenoidPin1 = 26   # Connected to relay to gate between furnace 2 and cooling area
Solenoid_Pin_3 = 21   # Meant to connect to furnace 1 gate currently disconnected

# position definition of gates 
gate1Position = 2.5	  # Defines stage between Furnace2(2) and Cooling(3)
gate3Position = 0.5      # CURRENTLY UNUSED Furnace1(1) and Top(0)

# define a safety clearance before the sample hits the gate
safetyClearance = 0.015

# Initialize and set-up GATE solenoid pins
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(solenoidPin1, GPIO.OUT)
GPIO.setup(Solenoid_Pin_3, GPIO.OUT)
GPIO.output(solenoidPin1, GPIO.LOW)
GPIO.output(Solenoid_Pin_3, GPIO.LOW)

samplePosition = [util.read_poten(potenChannel)] 
samplePosition.append(None)

# Control the gate pased on movement and stage transitions
def gateControl(startStage, endStage):

	#print "startStage => %r" %startStage
	#print "endStage => %r" %endStage
	
	if ((startStage < gate1Position) and (endStage > gate1Position)):
		GPIO.output(solenoidPin1, GPIO.HIGH)
		#print "open up"
		time.sleep(0.5)
	elif ((startStage > gate1Position) and (endStage < gate1Position)):
		GPIO.output(solenoidPin1, GPIO.HIGH)
		#print "open down"
		time.sleep(0.5)
	else:
		GPIO.output(solenoidPin1, GPIO.LOW)
		#print "close up/down"
		time.sleep(0.5)

# Gate testing
def test_open_close_gate():
	print "TEST: open gate"
	GPIO.output(solenoidPin1, GPIO.HIGH)
	time.sleep(1.0)
	
	print "TEST: close gate"
	GPIO.output(solenoidPin1, GPIO.LOW)
	time.sleep(1.0)
	
	print "TEST: open gate"
	GPIO.output(solenoidPin1, GPIO.HIGH)
	time.sleep(1.0)
	
	print "TEST: close gate"
	GPIO.output(solenoidPin1, GPIO.LOW)
	time.sleep(1.0)
	
# Starts the thread in main()
def gateThread():
	
	while True:
		
		# for testing gate operation
		#test_open_close_gate()
		
		samplePosition[1] = util.read_poten(potenChannel)
		
		# for testing potentiometer readings
		#print "sample start position = %r" %sample_position[0]
		#print "sample end position = %r" %sample_position[1]
		
		
		# sample is moving
		if samplePosition[0] != samplePosition[1]:
			# This cascading (confusing) if-statement reduces a margin of noise causing the gate to occasionally jump
			if (samplePosition[0] > samplePosition[1] + 0.001 and samplePosition[0] < samplePosition[1]+0.02) or (samplePosition[0] < samplePosition[1] - 0.001 and samplePosition[0] > samplePosition[1]-0.02) :
				time.sleep(0.1)
			else :
				gateControl(STM.startStage, STM.endStage)
				time.sleep(0.1)
			
			
		# sample is not moving
		
		else :
			#close the gate
			time.sleep(0.5)
			GPIO.output(solenoidPin1, GPIO.LOW)
	
		samplePosition[0] = samplePosition[1]
		time.sleep(0.01)

		

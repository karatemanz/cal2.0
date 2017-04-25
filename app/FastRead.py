# Fast reading data from mcp3208 and IR sensors for accurate data collection

import numpy as np
import matplotlib.pyplot as plt
import spidev
import time
import os
import RPi.GPIO as GPIO
from pylab import *

import furnace_control as fc

# Set-up solenoid cooling valve
solenoid_valve_pin = 13
GPIO.setmode(GPIO.BCM)
GPIO.setup(solenoid_valve_pin, GPIO.OUT)
GPIO.output(solenoid_valve_pin, GPIO.LOW)

# Open SPI bus
spi = spidev.SpiDev()
spi.open(0,0)

# Define a temperature padding to compensate for precision error 
# when averaging during sensor data collection
heatPad = 2
coolPad = 5

# Perform a quick read on the furnace collecting data in the process
def fastReadFurnace(frequency, startTemp, endTemp, fchannel, hold, tab, tabTotal, lastTime):
	
	print lastTime
	
	delay = 1.0/frequency
	
	# Create two lists to hold time and sample temperature
	tempLevels  = []
	elapsedTime = []
	runTime = 0
	offset = 0
	
	if lastTime != 0:
		offset = lastTime
		
	# A ramp in temperature is specified
	if startTemp != endTemp:
		print "setting furnace to desired end temperature..."
		if fchannel == util.F1Channel:
			util.setFurnace1Temp(endTemp)
		elif fchannel == util.F2Channel:
			util.setFurnace2Temp(endTemp)
	
	# A hold in temperature is specified		
	else:
		print "Begin sample heat treatment and data collection"
		runTime = time.time()
		print "collecting data..."
		while hold > 0:
			
			# collect current temperature and time
			curTemp = util.read3208(fchannel)
			curTime = round((time.time() - runTime) + offset, 4)
			
			# log captured data and graph accordingly
			elapsedTime.append(curTime)
			tempLevels.append(curTemp)
			tab.addRowToGrid(curTime, curTemp)
			tabTotal.addRowToGrid(curTime, curTemp)
			tab.plotPoint(curTime, curTemp)
			tabTotal.plotPoint(curTime, curTemp)
			
			# wait one second and decremet the hold count
			time.sleep(1)
			hold -= 1
			lastTime = (time.time() - runTime) + offset
		
		print "Finished... data collected, summary:"
		print "Time:        %r" %elapsedTime[0:5]
		print "Temperature: %r"	%tempLevels[0:5]
		
		print "collection ends at %r seconds" %int(time.time() - runTime)
		
		return elapsedTime, tempLevels, lastTime
				
	upperEndTemp = endTemp + heatPad
	lowerEndTemp = endTemp - heatPad
	curTemp = util.read3208(fchannel)
	
	runTime = time.time()
	# Continue reading until sample reaches the desired END TEMP
	while curTemp < lowerEndTemp or curTemp > upperEndTemp or curTemp <= 250:
		 
		# collect current temperature and time
		curTemp = util.read3208(fchannel)
		curTime = round((time.time() - runTime) + offset, 4)
		 
		print "[IR] reading sample until end temp {} from {}".format(endTemp, curTemp)
		 
		# log captured data and graph accordingly
		elapsedTime.append(curTime)
		tempLevels.append(curTemp)
		tab.addRowToGrid(curTime, curTemp)
		tabTotal.addRowToGrid(curTime, curTemp)
		tab.plotPoint(curTime, curTemp)
		tabTotal.plotPoint(curTime, curTemp)
		 
		# delay at the desired frequency rate  
		time.sleep(delay)
		lastTime = (time.time() - runTime) + offset
		 
	print "Finished... data collected, summary:"
	print "Time:        %r" %elapsedTime[0:5]
	print "Temperature: %r"	%tempLevels[0:5]
		
	print "collection ends at %r seconds" %int(time.time() - runTime)
		
	return elapsedTime, tempLevels, lastTime

# Perform a quick read on the cooling process	
def fastReadCooling(frequency, startTemp, endTemp, cchannel, tab, tabTotal, lastTime):
	
	print lastTime
	
	delay = 1.0/frequency
	
	# Create two lists to hold time and sample temperature
	tempLevels  = []
	elapsedTime = []
	runTime = 0
	offset = 0
	
	if lastTime != 0:
		offset = lastTime
	
	# IR sensor is currently restricted to 250 degrees Celsius on the lower end
	# of the temperature spectrum [I'd suggest a sensor more within range 23 -> 1000 C, but budgets :(]
	if endTemp < 250:
		endTemp = 250
	
	upperEndTemp = endTemp + coolPad
	lowerEndTemp = endTemp - coolPad
	curTemp = util.read3208(cchannel)
	
	print "collecting data..."
	runTime = time.time()
	# Continue reading until sample hits the desired END TEMP
	while curTemp > upperEndTemp:
		
		# collect current temperature and time
		curTemp = util.read3208(cchannel)
		curTime = round((time.time() - runTime) + offset, 4)
		
		print "reading sample until end temp {} from {}".format(endTemp, curTemp)
		
		# log captured data and graph accordingly
		elapsedTime.append(curTime)
		tempLevels.append(curTemp)
		tab.addRowToGrid(curTime, curTemp)
		tabTotal.addRowToGrid(curTime, curTemp)
		tab.plotPoint(curTime, curTemp)
		tabTotal.plotPoint(curTime, curTemp)
		
		# delay at the desired frequency rate
		time.sleep(delay)
		lastTime = (time.time() - runTime) + offset 
	
	print "Finished... data collected, summary:"
	print "Time:        %r" %elapsedTime[0:5]
	print "Temperature: %r" %tempLevels[0:5]
	
	if len(elapsedTime) > 0:
		# compute the simulations cooling rate
		coolingRate = abs(tempLevels[-1]-tempLevels[0])/abs(elapsedTime[-1]-elapsedTime[0])
		print "Cooling rate: {} with a sample from: {}, to: {}".format(coolingRate, startTemp, endTemp) 
	
	print "collection ends at %r seconds" %int(time.time() - runTime)
	
	return elapsedTime, tempLevels, lastTime	
	
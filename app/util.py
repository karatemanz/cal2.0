import STM
import furnace_control as fc
import spidev

spi = spidev.SpiDev()
spi.open(0,0)

F1Channel = 4
CoolChannel = 3
F2Channel = 0

Furnace_1 = 1
Cool = 2
Furnace_2 = 3
Load = 4

F1Address = 01
F2Address = 02

Vref = 4.96

# --------------------------------------------------------------------------------------------------------------------
#  General Utilities
# --------------------------------------------------------------------------------------------------------------------

# Create Total Time Sequence (ex. furnace 1 goes from 500 to 600 degrees at 10 second rate Temps: [500, 600] Times: [0, 10])
def parseTimeSequence(times):
	
	sequence = []
	totalTime = 0
	prevTime = 0
	
	if len(times) != 0:
		
		for time in times:
			
			sequence.append(prevTime)
			totalTime += time
			sequence.append(totalTime)
			prevTime = totalTime
	
						
	# append a 0 to the front of the list			
	return sequence

# convert string to in
def converttoint(s):
    if not isinstance(s, basestring):
        return str(s)
    if s.isdigit():
        return int(s, 16)
    try:
        return float(s)
    except ValueError:
        return None

# to convert time interval list into a list of time coordinates for drawing the presets
def newlist(l):
	for i in range(len(l)):
		if i != 0:
			l[i] = l[i] +l[i-1]
	return l

# convert a number to string representation of the number
def dig_convert(number, n):
	number = str(number)
	while len(number) < n:
		number = '0' + number
	return number

# convert a number to the hex representation of the number
def hex_convert(number):
	number = hex(number)[2:]
	if len(number) > 4 :
		print "Value more than FFFF, invalid"
	else:
		while len(number) < 4:
			number = '0' + number
		#print number
		return number

# --------------------------------------------------------------------------------------------------------------------
#  Analog-to-Digital Reading Utilities
# --------------------------------------------------------------------------------------------------------------------

# Used for reading the temperature of the IR sensors AND for reading the potentiometer connected to the Stepper Motor
def read3208(channel):
	data = ReadChannel_12bit(channel)
	volt = ConvertVolts_12bit(data, 4)
	# Omega (Furnace 2)
	if channel == F2Channel:
		# this sensor was about to be replaced upon the ending of our senior design period
		temp = round((210.6061*(volt*330/653.7))-163, 2)
	# Pyrospot (Furnace 1)
	if channel == F1Channel:
		temp =  round((401.621787*volt*330/653.7-12.5),2)
	# Pyrospot (Cooling Area)	
	if channel == CoolChannel:
		temp =  round((402.705314*volt*330/653.7-12.5),2)
	return temp

# Read the potentiometer
def read_poten(channel):
	data = ReadChannel_12bit(channel)
	volt = ConvertVolts_12bit(data, 2)
	
	## use volt above to calculate the position of the sample
	sample_pos = volt
	return sample_pos	
	
# Read averaged voltage 12-bit data readings from MCP3208 ADC
def ReadChannel_12bit(channel):
	adc = spi.xfer2([6 | (channel >> 2), (channel & 3) << 6, 0])
	data = ((adc[1] & 15)<< 8) + adc[2]
	return data

# Convert the data to volts
def ConvertVolts_12bit(data, places):
	# When using MCP3208(12 bit adc)
	volts = (data*Vref)/float(4096)
	volts = round(volts, places)
	return volts

# --------------------------------------------------------------------------------------------------------------------
#  Simplified Stage-To-Stage Sample Movement Utilities
# --------------------------------------------------------------------------------------------------------------------

# Move sample to the first furnace and mark new stage
def moveToFurnace1(self):
	STM.startStage = STM.RelativeStepper(self.motorSpeed, self.sample, STM.Furnace_1)

# Move sample to the cooling area  and mark new stage
def moveToCoolingArea(self):
	STM.startStage = STM.RelativeStepper(self.motorSpeed, self.sample, STM.Cool)

# Move sample to furnace 2 and mark new stage	
def moveToFurnace2(self):
	STM.startStage = STM.RelativeStepper(self.motorSpeed, self.sample, STM.Furnace_2)

# Move sample to loading position and mark new stage
def moveToLoad(self):
	STM.startStage = STM.RelativeStepper(self.motorSpeed, self.sample, STM.Load)
	
# Stages new samples for accurate positioning	
def stageSample(self):
	STM.startStage = STM.LoadStepper(self.motorSpeed, self.sample)

# --------------------------------------------------------------------------------------------------------------------
#  Simplified Furance Interfacing Utilities
# --------------------------------------------------------------------------------------------------------------------

# Set furnace 1's set point temperature
def setFurnace1Temp(temp):
	fc.setTemp("01", temp, fc.ser)
	
# Set furnace 1's ramp and direction C/sec		
def setFurnace1Ramp(ramp, rdir):
	rampMin = ramp
	fc.setRamp(F1Address, rampMin, rdir, fc.ser)

# Get furnace 1's temperature	
def getFurnace1Temp():
	hexTemp = fc.getPV("01", fc.ser)
	
	# While the furnace is not ready to return a temperature or busy
	while CR not in hexTemp or hexTemp[7:11] == '' or hexTemp[7:11] == '\x03\r': 
		hexTemp = fc.getPV("01", fc.ser)
	
	hexTemp = hexTemp[7:11]
	temp = int(hexTemp, 16)
	
	return temp
	
# Get furnace 1's current up ramp value	
def getFurnace1UpRamp():
	hex_temp = fc.getUPR("01", fc.ser)[7:11]
	temp = int(hex_temp,16)
	return temp

# Get furnace 1's current down ramp value
def getFurnace1DownRamp():			
	hex_temp = fc.getDNR("01", fc.ser)[7:11]
	temp = int(hex_temp,16)
	return temp

# Get furnace 1's current set point temperature
def getFurance1SetPoint():
	hex_temp = fc.getCSP("01", fc.ser)[7:11]
	temp = int(hex_temp,16)
	return temp		
		
# Set furnace 2 temp		
def setFurnace2Temp(temp):
	fc.setTemp("02", temp, fc.ser)
	
# Set furnace 2 ramp value and direction C/sec	
def setFurnace2Ramp(ramp, rdir):
	rampMin = ramp
	fc.setRamp(F2Address, rampMin, rdir, fc.ser)

# Get furnace 2's temperature	
def getFurnace2Temp():
	hexTemp = fc.getPV("02", fc.ser)
	
	# While the furnace is not ready to return a temperature or busy
	while CR not in hexTemp or hexTemp[7:11] == '' or hexTemp[7:11] == '\x03\r': 
		hexTemp = fc.getPV("02", fc.ser)
	
	hexTemp = hexTemp[7:11]
	temp = int(hexTemp, 16)
	
	return temp
	
# Get furnace 2 set point temperature
def getFurnace2SetPoint():
	hex_temp = fc.getCSP("02", fc.ser)[7:11]
	temp = int(hex_temp,16)
	return temp	

# Get furnace 2's up ramp value
def getFurnace2UpRamp():
	hex_temp = fc.getUPR("02", fc.ser)[7:11]
	temp = int(hex_temp,16)
	return temp

# Get furnace 2's down ramp value	
def getFurnace2DownRamp():	
	hex_temp = fc.getDNR("02", fc.ser)[7:11]
	temp = int(hex_temp,16)
	return temp

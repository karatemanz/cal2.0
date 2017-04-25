import serial
import util

# defined for furnace operations
addr = 0x04  
STX = chr(2)
ETX = chr(3)
CR = chr(13)

# Define serial port for serial communications with the furnaces
#ser = serial.Serial(
#				port = '/dev/ttyUSB0',
#				baudrate = 9600,
#				bytesize = serial.EIGHTBITS,
#				parity = serial.PARITY_EVEN,
#				stopbits = serial.STOPBITS_ONE,
#				timeout = 0.2
#				)

# read result of a command to the furnace
def readlineCR(port):
	rv = ""
	count = 0
	while count != 30:
		ch = port.read()
		rv += ch
		
		#print "RV %r" %rv
		
		if ch == CR:
			return rv
		
		count+=1	
	return rv		
			
# get the TEMPERATURE of the furance
def getPV(slave, port):
	port.write(STX+slave+"010WRDD0002,01"+ETX+CR)
	return readlineCR(port)

# get the CURRENT SET POINT of the furnace
def getCSP(slave, port):
	port.write(STX+slave+"010WRDD0120,01"+ETX+CR)
	return readlineCR(port)

# get the UP RAMP of the furnace
def getUPR(slave, port):
	port.write(STX+slave+"010WRDD0201,01"+ETX+CR)
	return readlineCR(port)

# get the DOWN RAMP of the furnace
def getDNR(slave, port):
	port.write(STX+slave+"010WRDD0202,01"+ETX+CR)
	return readlineCR(port)

# CURRENTLY UNUSED:
def getPID_P(slave, port):
	port.write(STX+slave+"010WRDD0105,01"+ETX+CR)
	return readlineCR(port)

# CURRENTLY UNUSED:
def getPID_I(slave, port):
	port.write(STX+slave+"010WRDD0106,01"+ETX+CR)
	return readlineCR(port)

# CURRENTLY UNUSED:
def getPID_D(slave, port):
	port.write(STX+slave+"010WRDD0107,01"+ETX+CR)
	return readlineCR(port)

# set the CURRENT SET POINT temperature of the furnace
def setTemp(slave, tempsf1, port):
	#Master_Number = "01"
	Slave_Address = dig_convert(slave, 2)
	message = STX+Slave_Address+"01"+"0"+"WRW"+"01"+"D0114,"+str(util.hex_convert(tempsf1)).upper()+ETX+CR
	port.write(message)

# set the CURRENT UP or DOWN RAMP fo the furnace
def setRamp(slave, Ramp, UD, port):
	#Master_Number = "01"
	Slave_Address = dig_convert(slave, 2)
	if UD == 1:
		D_Register = "D0201,"
		message = STX+Slave_Address+"01"+"0"+"WRW"+"01"+D_Register+str(util.hex_convert(Ramp)).upper()+ETX+CR
		print "setRamp UP"
		port.write(message)

	elif UD == -1:
		D_Register = "D0202,"
		message = STX+Slave_Address+"01"+"0"+"WRW"+"01"+D_Register+str(util.hex_convert(Ramp)).upper()+ETX+CR
		print "setRamp DOWN"
		port.write(message)
	

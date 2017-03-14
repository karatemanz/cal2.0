# wxpython menu&toolbar practice
# IR_sensor Branch
import csv
import threading

import RPi.GPIO as GPIO
import matplotlib
import pandas as pd
import serial
import wx.aui
import wx.lib.agw.flatnotebook as fnb
import wx.lib.intctrl
import wx.lib.scrolledpanel

matplotlib.interactive( True )
matplotlib.use('WXAgg')
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from optimizing.m2m_interface_code.solenoid_thread_test import *

from optimizing.ui_components import mygrid, panelFive, panelThree, tempSettingTwo, panelOne, panelTwo, tempSettingOne, \
	panelFour, GasQuenching
from optimizing.m2m_interface_code.STM import *
from optimizing.m2m_interface_code.RPI_I2C_ARDUINO import *
from optimizing.m2m_interface_code.FastRead import *

addr = 0x04  
STX = chr(2)
ETX = chr(3)
CR = chr(13)
Overshoot = 0.0 # small sample
#Overshoot = 0.04 # small sample
#Overshoot = 0.03 # large sample

Vref = 4.96*(653.7/330.0)
counter = 0
solenoid_valve_pin = 13
IR_sensor_pin = 19

# RASPBERRY PI SETUP
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(solenoid_valve_pin, GPIO.OUT)
GPIO.setup(IR_sensor_pin, GPIO.OUT)
GPIO.output(solenoid_valve_pin, GPIO.LOW)
GPIO.output(IR_sensor_pin, GPIO.LOW)


ser = serial.Serial(
				port = '/dev/ttyUSB0',
				baudrate = 9600,
				bytesize = serial.EIGHTBITS,
				parity = serial.PARITY_EVEN,
				stopbits = serial.STOPBITS_ONE,
				timeout = 0.2
				)

Heating = [['time', 'furnace 1 temp', 'current set point temp', 'thermocouple temp']]
Reheating = [['time', 'furnace 2 temp', 'thermocouple temp']]
FCECool = [['time', 'thermocouple temp']]
Cooling = ['time', 'temp']

# Thread testing
def do_this():
	print "this means the thread2 is running"

# READ THERMOCOUPBLE temperature from (mcp3008+ad8495) module
def read3008(channel):
	data = ReadChannel_10bit(channel) # ReadChannel is defined in FastRead.py, assume thermocouple is on channel 0
	volt = ConvertVolts_10bit(data, 4)

	# Voltage divider, R1+R2 = 653.7, R2=330, Y = (R1+R2)/R2 = 1.980909
	temp = round((volt - 1.25)/0.005, 4)
	print data, volt, temp
	return temp

# READING FURNACE SENSORS
# NEW: read temperature from (mcp3208+ad8495) module
def read3208(channel):
	data = ReadChannel_12bit(channel)
	volt = ConvertVolts_12bit(data, 4)

	# using IR sensor SI23
	#temp = (volt*1000/165.0-0.8)/(8.0/375.0)
	# Channel 0 -> Thermocouple Sensing (Bottom Furnace)
	# Channel 4 -> IR Sensing (Cooling Area)?
	# Channel 3 -> IR Sensing (Top Furnace)?
	if channel == 0:
		temp = round((volt - 1.25)/0.005, 4)
	if channel == 4:
		temp = round((401.621787*volt*330/653.7-12.5),2)
	if channel == 3:
		temp = round((402.705314*volt*330/653.7-12.5),2)

	print("Temperature Reading: " + temp)
	return temp

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

# find the largest value ins a list and their position in the list
def list_biggest(x, y): # x is the list, y is the modify factor
	j = [0]
	j.append(None)
	a = 0

	k = [0]
	k.append(None)

	for i in range(len(x)):
		if x[i] == max(x):
			j[a] = i
			a += 1
	for i in range(len(j)):
		k[i] = x [j[i]]
		x[j[i]] = round(x[j[i]]*y, 2)
	return x,k,j

# use stepper motor to move sample along the strip
def RunStepper(position, speed, SampleLength, position_num):

	# convert distance unit mm to stepper motor's microsteps
	# 1 stepper motor step equals 1.8 degree,
	# 16 micro-steps equals 1 step
	if position_num == 1:
		x = 1800
	elif position_num == 2:
		x = 1490
	elif position_num == 3:
		x = 1080
	elif position_num == 4:
		x = 750

	# calculate the distance the sample should travel
	distance_ = int(float(x - position-SampleLength)*(3200/(math.pi*110.4)))
	distance_ = str(distance_)
	Distance = distance_ + 'Dis'

	# calculate the speed the stepper motor should rotate
	# convert speed unit rpm to stepper motor's microsteps/sec
	speed_ = int(float(speed)*(3200/60))
	speed_ = str(speed_)
	Speed = speed_ + 'Spd'

	# calculate position of the sample
	position = str(position_num) + 'P'
	direct = '1' + 'E'# 'E' stands for end.

	# sets the command to be processed
	cmd = Distance + Speed + position + direct
	communication_send(addr, "stm", cmd)

def dig_convert(number, n):
	number = str(number)
	while len(number) < n:
		number = '0' + number
	return number

def hex_convert(number):
	number = hex(number)[2:]
	if len(number) > 4 :
		print "Value more than FFFF, invalid"
	else:
		while len(number) < 4:
			number = '0' + number
		#print number
		return number

def readlineCR(port):
	rv = ""
	while 1:
		ch = port.read()
		rv += ch
		if ch == '\r' or ch == CR:
			return rv

def getPV(slave, port):
	port.write(STX+slave+"010WRDD0002,01"+ETX+CR)
	return  readlineCR(port)

def getCSP(slave, port):
	port.write(STX+slave+"010WRDD0120,01"+ETX+CR)
	return  readlineCR(port)

def getUPR(slave, port):
	port.write(STX+slave+"010WRDD0201,01"+ETX+CR)
	return  readlineCR(port)

def getDNR(slave, port):
	port.write(STX+slave+"010WRDD0202,01"+ETX+CR)
	return  readlineCR(port)

def getPID_P(slave, port):
	port.write(STX+slave+"010WRDD0105,01"+ETX+CR)
	return  readlineCR(port)

def getPID_I(slave, port):
	port.write(STX+slave+"010WRDD0106,01"+ETX+CR)
	return  readlineCR(port)

def getPID_D(slave, port):
	port.write(STX+slave+"010WRDD0107,01"+ETX+CR)
	return  readlineCR(port)

def setTemp(slave, temps1, port):
	#Master_Number = "01"
	Slave_Address = dig_convert(slave, 2)
	message = STX+Slave_Address+"01"+"0"+"WRW"+"01"+"D0114,"+str(hex_convert(temps1)).upper()+ETX+CR
	port.write(message)
	#print readlineCR(port)

def setRamp(slave, Ramp, UD, port):
	#Master_Number = "01"
	Slave_Address = dig_convert(slave, 2)
	if UD == 1:
		D_Register = "D0201,"
		message = STX+Slave_Address+"01"+"0"+"WRW"+"01"+D_Register+str(hex_convert(Ramp)).upper()+ETX+CR
		#message2 = STX+Slave_Address+"01"+"0"+"WRW"+"01"+"D0202,"+str(hex_convert(Ramp)).upper()+ETX+CR
		#print "setRamp"
		port.write(message)
		#print readlineCR(port)[1:]
		#port.write(message2)
		#print readlineCR(port)[1:]
	elif UD == -1:
		D_Register = "D0202,"
		message = STX+Slave_Address+"01"+"0"+"WRW"+"01"+D_Register+str(hex_convert(Ramp)).upper()+ETX+CR
		#message2 = STX+Slave_Address+"01"+"0"+"WRW"+"01"+"D0201,"+str(hex_convert(Ramp)).upper()+ETX+CR
		#print "setRamp"
		port.write(message)
		#print readlineCR(port)[1:]
		#port.write(message2)
		#print readlineCR(port)[1:]


# creating Notebook class
class Notebook(fnb.FlatNotebook):
	def __init__(self, parent):
		windowstyle = fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NO_X_BUTTON
		fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY, agwStyle=windowstyle)

		self.SetTabAreaColour('white')
		#self.SetActiveTabTextColour('black')
		self.tabOne = panelOne.TabPanel(self)
		self.tabTwo = panelTwo.TabPanel(self)
		self.tabThree = panelThree.TabPanel(self)
		self.tabFour = panelFour.TabPanel(self)
		self.tabFive = panelFive.TabPanel(self)

		self.AddPage(self.tabOne, "Furnace One")
		self.AddPage(self.tabTwo, "Furnace Two")
		self.AddPage(self.tabThree, "Cooling Process") 
		self.AddPage(self.tabFour, "Furnace Cooling") 
		self.AddPage(self.tabFive, "Total Treatment History") 

class Notebook2(fnb.FlatNotebook):
	def __init__(self, parent):
		windowstyle = fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NO_X_BUTTON
		fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY, agwStyle=windowstyle)	
		self.parent = parent
		#self.SetActiveTabTextColour('black')
		
		self.tabOne = tempSettingOne.TabPanel(self)
		self.tabTwo = tempSettingTwo.TabPanel(self)
		self.tabThree = GasQuenching.TabPanel(self)

		self.AddPage(self.tabOne, "Furnace One")
		self.AddPage(self.tabTwo, "Furnace Two")
		self.AddPage(self.tabThree, "Cooling Setting")

class CanvasPanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.figure = Figure()
        self.axes = self.figure.add_subplot(111)
        self.canvas = FigureCanvas(self, -1, self.figure)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
        self.SetSizer(self.sizer)
        self.Fit()

    def draw(self):
        t = arange(0.0, 3.0, 0.01)
        s = sin(2 * pi * t)
        self.axes.plot(t, s)

class RandomPanel(wx.Panel):
    """"""
    #----------------------------------------------------------------------
    def __init__(self, parent, color):
        """Constructor"""
        wx.Panel.__init__(self, parent)
        self.SetBackgroundColour(color)

class MainFrame(wx.Frame):

	def __init__(self, parent, title):
		super(MainFrame, self).__init__(parent, title=title, size=wx.DisplaySize())
		self.mgr = wx.aui.AuiManager(self)
		self.InitUI()
		self.Centre()
		self.RunFlag = 0

	def InitUI(self):

		self.ymin2 = 0
		self.cooling_ready = 0
		self.cooling_gap_timer = 0
		self.flag = 0
		self.Furnace2Lock = 0
		self.Peak_HoldingTime = 0
		self.IBHT_HoldingTime = 0 
		self.Furnace1_Temp = []
		self.j1 = []
		self.ADC_Temp = []
		self.Furnace2_Temp = []
		self.Run_Time = []

		imagesPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

		# creating a toolbar MENU BAR
		toolbar = self.CreateToolBar()
		tool1 = toolbar.AddLabelTool(wx.ID_ANY, 'New'
			, wx.Bitmap(os.path.join(imagesPath, 'images/new3.png')))
		tool2 = toolbar.AddLabelTool(wx.ID_ANY, 'Open'
			, wx.Bitmap(os.path.join(imagesPath, 'images/open3.png')))
		tool3 = toolbar.AddLabelTool(wx.ID_ANY, 'Save'
			, wx.Bitmap(os.path.join(imagesPath, 'images/save3.png')))
		tool4 = toolbar.AddLabelTool(wx.ID_ANY, 'Print'
			, wx.Bitmap(os.path.join(imagesPath, 'images/printer3.png')))
		tool5 = toolbar.AddLabelTool(wx.ID_ANY, 'Setting'
			, wx.Bitmap(os.path.join(imagesPath, 'images/setting.png')))
		tool6 = toolbar.AddLabelTool(wx.ID_ANY, 'Quit'
			, wx.Bitmap(os.path.join(imagesPath, 'images/exit3.png')))
		toolbar.SetToolBitmapSize((16,16))
		toolbar.Realize()

		# creating panes 
		self.sampleControlPanel =sampleControlPanel= wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=-1, size=(340, 100))

		#simulationDataPanel = wx.Panel(self, -1, size=(200, 205))
		self.simulationDataPanel =simulationDataPanel= mygrid.MyGrid(self)

		graphPanel = wx.Panel(self, -1, size=(600, 400))
		graphPanel.SetBackgroundColour('white')

		self.panel4 = statusPanel = wx.Panel(self, -1, size=(200, 100))
		#panel5 = wx.Panel(self, -1, size=(200, 100))
#--------------------------------------------------------------------------------------------
#for sampleControlPanel(leftpane) which is on the left
		sampleControlPanel.SetupScrolling()
		self.leftpane= leftpane = sampleControlPanel

		# creating a static box in leftpane
		leftsizer = wx.BoxSizer(wx.VERTICAL)

		sampleSettings = wx.StaticBox(leftpane,label='Basic Settings',style=wx.TE_CENTRE)
		sampleSettings.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.sl = wx.lib.intctrl.IntCtrl(leftpane, 90, 190, size=(40, -1),style=wx.TE_RIGHT)
		self.setSampleLengthButton = wx.Button(leftpane, label='SET', size=(40, -1))
		sampleSettingsSizer = wx.StaticBoxSizer(sampleSettings, wx.HORIZONTAL)
		sampleSettingsSizer.Add(wx.StaticText(leftpane, label="Sample Length:"), flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=5)
		sampleSettingsSizer.Add(self.sl, flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=3)
		sampleSettingsSizer.Add(wx.StaticText(leftpane, label="mm"), flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=5)
		sampleSettingsSizer.Add(self.setSampleLengthButton, flag=wx.LEFT | wx.ALIGN_RIGHT, border =95)

		motorSpeed = wx.StaticBox(leftpane,label='Sample Transportation',style=wx.TE_CENTRE)
		motorSpeed.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.sms = wx.lib.intctrl.IntCtrl(leftpane, 91, 120, size=(40, -1),style=wx.TE_RIGHT)
		self.setMotorSpeed = wx.Button(leftpane, label='SET', size=(40, -1))
		positioningSizer = wx.StaticBoxSizer(motorSpeed, wx.HORIZONTAL)
		positioningSizer.Add(wx.StaticText(leftpane, label="Stepper Mottor Speed:"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		positioningSizer.Add(self.sms,flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=3)
		positioningSizer.Add(wx.StaticText(leftpane, label="rpm"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		positioningSizer.Add(self.setMotorSpeed, flag=wx.LEFT | wx.ALIGN_RIGHT, border =48)

		# creating a separating line between two staticbox
		line1 = wx.StaticLine(leftpane)
		line2 = wx.StaticLine(leftpane)
		line3 = wx.StaticLine(leftpane)

		sampleStopPoint = wx.StaticBox(leftpane,label='Sample Stop Point (mm)',style=wx.TE_CENTRE)
		sampleStopPoint.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		stopPointSizer = wx.StaticBoxSizer(sampleStopPoint, wx.VERTICAL)

		samplePositionSizer = wx.GridBagSizer(1, 4)

		# using gridbadsizer to arrange the sliders inside staticbox2(sampleStopPoint)
		# notebook2 for temperature setting
		self.notebook2 = Notebook2(sampleControlPanel)
		tempsettingSizer = wx.BoxSizer(wx.VERTICAL)
		tempsettingSizer.Add(self.notebook2, 1, flag = wx.ALL|wx.EXPAND)

		#-------------------------------------------------------------------------------------
		# Set the slider controls for sample position calibration

		self.preview1 = wx.Button(leftpane, label='Preview 1', size=(55, -1))
		self.positionSlider1 = positionSlider1 = wx.Slider(leftpane, value=0, minValue=0, maxValue=350, size=(-1, 130), style=wx.SL_VERTICAL | wx.SL_LEFT)
		self.ssp1 = wx.lib.intctrl.IntCtrl(leftpane, 100, 0, size=(30, -1), min=0, max=350, style=wx.TE_CENTRE)
		samplePositionSizer.Add(positionSlider1, pos=(1, 1), flag=wx.LEFT, border=14)
		samplePositionSizer.Add(wx.StaticText(leftpane, label="SSP 1:"), pos=(2, 1),flag=wx.LEFT, border=7)
		samplePositionSizer.Add(self.ssp1, pos=(3, 1), flag=wx.EXPAND)
		samplePositionSizer.Add(self.preview1, pos=(4, 1), flag=wx.EXPAND)


		self.preview2 = wx.Button(leftpane, label='Preview 2', size=(55, -1))
		self.positionSlider2 = positionSlider2 = wx.Slider(leftpane, value=0, minValue=0, maxValue=410, size=(-1, 130), style=wx.SL_VERTICAL | wx.SL_LEFT)
		self.ssp2 = wx.lib.intctrl.IntCtrl(leftpane, 101, 0, size=(30, -1), min=0, max=410, style=wx.TE_CENTRE)
		samplePositionSizer.Add(positionSlider2, pos=(1, 3), flag=wx.EXPAND)
		samplePositionSizer.Add(wx.StaticText(leftpane, label="SSP 2:"), pos=(2, 3),flag=wx.LEFT, border=7)
		samplePositionSizer.Add(self.ssp2, pos=(3, 3), flag=wx.EXPAND)
		samplePositionSizer.Add(self.preview2, pos=(4, 3), flag=wx.EXPAND)


		self.preview3 = wx.Button(leftpane, label='Preview 3', size=(55, -1))
		self.positionSlider3 = positionSlider3 = wx.Slider(leftpane, value=0, minValue=0, maxValue=330, size=(-1, 130), style=wx.SL_VERTICAL | wx.SL_LEFT)
		self.ssp3 = wx.lib.intctrl.IntCtrl(leftpane, 102, 0, size=(30, -1), min=0, max=330, style=wx.TE_CENTRE)
		samplePositionSizer.Add(positionSlider3, pos=(1, 5), flag=wx.EXPAND)
		samplePositionSizer.Add(wx.StaticText(leftpane, label="SSP 3:"), pos=(2, 5),flag=wx.LEFT, border=7)
		samplePositionSizer.Add(self.ssp3, pos=(3, 5), flag=wx.EXPAND)
		samplePositionSizer.Add(self.preview3, pos=(4, 5), flag=wx.EXPAND)

		self.preview4 = wx.Button(leftpane, label='Preview 4', size=(55, -1))
		self.positionSlider4 = positionSlider4 = wx.Slider(leftpane, value=0, minValue=0, maxValue=750, size=(-1, 130), style=wx.SL_VERTICAL | wx.SL_LEFT)
		self.ssp4 = wx.lib.intctrl.IntCtrl(leftpane, 103, 0, size=(30, -1), min=0, max=750, style=wx.TE_CENTRE)
		samplePositionSizer.Add(positionSlider4, pos=(1, 7), flag=wx.EXPAND)
		samplePositionSizer.Add(wx.StaticText(leftpane, label="SSP 4:"), pos=(2, 7),flag=wx.LEFT, border=7)
		samplePositionSizer.Add(self.ssp4, pos=(3, 7), flag=wx.EXPAND)
		samplePositionSizer.Add(self.preview4, pos=(4, 7), flag=wx.EXPAND)

		stopPointSizer.Add(samplePositionSizer)
	
		leftsizer.Add(sampleSettingsSizer, 0, wx.EXPAND)
		leftsizer.Add(line1, 0, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border=5)
		leftsizer.Add(positioningSizer, 0, wx.EXPAND)
		leftsizer.Add(line2, 0, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border=5)
		leftsizer.Add(stopPointSizer, 0, wx.EXPAND)
		leftsizer.Add(line3, 0, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border=5)

		leftsizer.Add(tempsettingSizer, 0, wx.EXPAND)

		leftpane.SetSizer(leftsizer)
#---------------------------------------------------------------------------------------------
#for panel3(middlepane) which is on the centre
		self.notebook = Notebook(graphPanel)
		graphPanelSizer = wx.BoxSizer(wx.VERTICAL)

		#-------------------------------------------------------------------------------------
		# Set the sizers
		graphPanelSizer.Add(self.notebook, 1, flag = wx.ALL|wx.EXPAND)
		graphPanel.SetSizer(graphPanelSizer)
#---------------------------------------------------------------------------------------------
# statusPanel(Right Pane)
		statusPanelSizer = wx.BoxSizer(wx.VERTICAL)
		self.StartBox = wx.StaticBox(statusPanel,label='Furnace 1 Status',style=wx.TE_CENTRE)
		self.Furnace_num = 1
		self.StartBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box1 = wx.StaticBoxSizer(self.StartBox, wx.VERTICAL)
		#self.MainRun = wx.Button(statusPanel, label = 'Run',size=(190, 30))
		self.Furnace_switch = wx.Button(statusPanel, label = 'Switch Furnace',size=(190, 30))
		self.GetTemp = wx.Button(statusPanel, label = 'Current Temperature',size=(190, 30))
		self.GetCSP = wx.Button(statusPanel, label = 'Current Setpoint',size=(190, 30))
		#self.GetUPR = wx.Button(statusPanel, label="Current UpRamp", size = (190, 30))
		#self.GetDNR = wx.Button(statusPanel, label="Current DnRamp", size=(190, 30))
		#self.GetPID_P = wx.Button(statusPanel, label="P of PID", size=(190, 30))
		#self.GetPID_I = wx.Button(statusPanel, label="I of PID", size=(190, 30))
		#self.GetPID_D = wx.Button(statusPanel, label="D of PID", size=(190, 30))
		#panel4Box1.Add(self.MainRun, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.Furnace_switch, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.GetTemp, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.GetCSP, 0, wx.EXPAND, 0)
		#panel4Box1.Add(self.GetUPR, 0, wx.EXPAND, 0)
		#panel4Box1.Add(self.GetDNR, 0, wx.EXPAND, 0)
		#panel4Box1.Add(self.GetPID_P, 0, wx.EXPAND, 0)
		#panel4Box1.Add(self.GetPID_I, 0, wx.EXPAND, 0)
		#panel4Box1.Add(self.GetPID_D, 0, wx.EXPAND, 0)

		#panel4Box4 solenoid control
		self.ValveBox = wx.StaticBox(statusPanel,label='Solenoid Valve Off', style = wx.TE_CENTRE)
		self.ValveBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box4 = wx.StaticBoxSizer(self.ValveBox, wx.VERTICAL)
		self.ValveCon = wx.Button(statusPanel, label = 'Turn On',size=(190, 30))
		panel4Box4.Add(self.ValveCon, 0, wx.EXPAND, 0)

		#panel4box5 furnace preheat settings
		FurnacePresetBox = wx.StaticBox(statusPanel, label = 'Preheat Settings', style = wx.TE_CENTRE)
		FurnacePresetBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box5 = wx.StaticBoxSizer(FurnacePresetBox, wx.VERTICAL)
		#furnace 1 preset temp is stored in self.Fce1_preset
		self.Fce1_preset = wx.lib.intctrl.IntCtrl(statusPanel, 91, 0, size=(45, -1),style=wx.TE_RIGHT)
		self.Fce1_preset_BT = wx.Button(statusPanel, label = 'SET', size=(40, -1))

		#furnace 1 holding time is stored in self.Fc1_holdtime
		self.Fce1_holdtime = wx.lib.intctrl.IntCtrl(statusPanel, 91, 0, size=(45, -1),style=wx.TE_RIGHT)
		self.Fce1_holdtime_BT = wx.Button(statusPanel, label = 'SET', size=(40, -1))

		#furnace 2 preset temp is stored in self.Fce2_preset
		self.Fce2_preset = wx.lib.intctrl.IntCtrl(statusPanel, 90, 0, size=(45, -1),style=wx.TE_RIGHT)
		self.Fce2_preset_BT = wx.Button(statusPanel, label = 'SET', size=(40, -1))

		#furnace 2 holding time is stored in self.Fc1_holdtime
		self.Fce2_holdtime = wx.lib.intctrl.IntCtrl(statusPanel, 91, 0, size=(45, -1),style=wx.TE_RIGHT)
		self.Fce2_holdtime_BT = wx.Button(statusPanel, label = 'SET', size=(40, -1))

		FurnacePreset = wx.GridBagSizer(0, 5)
		FurnacePreset.Add(wx.StaticText(statusPanel, label="FCE 1 Temp:"), pos= (0, 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce1_preset, pos = (0, 1), flag=wx.BOTTOM, border=5)
		FurnacePreset.Add(wx.StaticText(statusPanel, label="C"), pos = (0, 2), flag=wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce1_preset_BT, pos = (0, 3), flag=wx.RIGHT|wx.BOTTOM, border=5)

		FurnacePreset.Add(wx.StaticText(statusPanel, label="FCE 1 Hold:"), pos= (1, 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce1_holdtime, pos = (1, 1), flag=wx.BOTTOM, border=5)
		FurnacePreset.Add(wx.StaticText(statusPanel, label="S"), pos = (1, 2), flag=wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce1_holdtime_BT, pos = (1, 3), flag=wx.RIGHT|wx.BOTTOM, border=5)

		FurnacePreset.Add(wx.StaticText(statusPanel, label="FCE 2 Temp:"), pos = (2, 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce2_preset, pos = (2, 1), flag=wx.BOTTOM, border=5)
		FurnacePreset.Add(wx.StaticText(statusPanel, label="C"), pos = (2, 2), flag=wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce2_preset_BT, pos = (2, 3), flag=wx.RIGHT|wx.BOTTOM, border=5)

		FurnacePreset.Add(wx.StaticText(statusPanel, label="FCE 2 Hold:"), pos= (3, 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce2_holdtime, pos = (3, 1), flag=wx.BOTTOM, border=5)
		FurnacePreset.Add(wx.StaticText(statusPanel, label="S"), pos = (3, 2), flag=wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.Fce2_holdtime_BT, pos = (3, 3), flag=wx.RIGHT|wx.BOTTOM, border=5)

		panel4Box5.Add(FurnacePreset, 0, flag = wx.TOP|wx.EXPAND)
		FurnacePresetBox.SetSizer(panel4Box5)
		panel4Box5.Fit(statusPanel)

		# Run BOX
		RunBox = wx.StaticBox(statusPanel,label='Start', style = wx.TE_CENTRE)
		RunBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box2 = wx.StaticBoxSizer(RunBox,wx.VERTICAL)
		self.MainRun = wx.Button(statusPanel, label = 'Run Furnace 1',size=(190, 30))
		self.Cooling = wx.Button(statusPanel, label = 'Start Cooling', size = (190, 30))
		self.Reheat = wx.Button(statusPanel, label = 'Run Furnace 2',size=(190, 30))
		self.FCECoolBT = wx.Button(statusPanel, label = 'Start FCE Cooling',size=(190, 30))
		panel4Box2.Add(self.MainRun, 0, flag = wx.TOP|wx.EXPAND)
		panel4Box2.Add(self.Cooling, 0, flag = wx.TOP|wx.EXPAND)
		panel4Box2.Add(self.Reheat, 0, flag = wx.TOP|wx.EXPAND)
		panel4Box2.Add(self.FCECoolBT, 0, flag = wx.TOP|wx.EXPAND)

		# Show total treatment history box
		self.ShowBox = wx.StaticBox(statusPanel, label = 'Total Plot', style = wx.TE_CENTRE)
		self.ShowBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box6 = wx.StaticBoxSizer(self.ShowBox, wx.VERTICAL)
		self.ShowPlot = wx.Button(statusPanel, label = 'Show Total Plot',size=(190, 30))
		panel4Box6.Add(self.ShowPlot, 0, wx.EXPAND, 0)

		# Test infor box
		TestInfoBox = wx.StaticBox(statusPanel, label='Test Info', style = wx.TE_CENTRE)
		TestInfoBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box3 = wx.StaticBoxSizer(TestInfoBox, wx.VERTICAL)
		self.TestInfo = wx.TextCtrl(statusPanel, size=(150, -1),style=wx.TE_RIGHT)
		panel4Box3.Add(wx.StaticText(statusPanel, label="Test Sample Number && Date :"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		panel4Box3.Add(self.TestInfo,0, flag = wx.TOP|wx.EXPAND)


		#-------------------------------------------------------------------------------------
		# Set the sizers
		statusPanelSizer.Add(panel4Box3, 0, flag = wx.TOP|wx.EXPAND, border=10)
		statusPanelSizer.Add(panel4Box1, 0, flag = wx.TOP|wx.EXPAND, border=10)
		statusPanelSizer.Add(panel4Box4, 0, flag = wx.TOP|wx.EXPAND, border=10)
		statusPanelSizer.Add(panel4Box5, 0,flag = wx.TOP|wx.EXPAND, border=10)
		statusPanelSizer.Add(panel4Box2, 0,flag = wx.TOP|wx.EXPAND, border=10)
		statusPanelSizer.Add(panel4Box6, 0,flag = wx.TOP|wx.EXPAND, border=10)

		statusPanel.SetSizer(statusPanelSizer)
#---------------------------------------------------------------------------------------------
		# using wx.aui to layout these created panes
		self.mgr.AddPane(simulationDataPanel, wx.aui.AuiPaneInfo().Bottom().CloseButton(False)
			.CaptionVisible(False))
		self.mgr.AddPane(sampleControlPanel, wx.aui.AuiPaneInfo().Left().Layer(1).CloseButton(False)
			.CaptionVisible(False))
		self.mgr.AddPane(graphPanel, wx.aui.AuiPaneInfo().Center().Layer(2).CloseButton(False)
			.CaptionVisible(False))
		self.mgr.AddPane(statusPanel, wx.aui.AuiPaneInfo().Right().Layer(1).CloseButton(False)
			.CaptionVisible(False))
		#self.mgr.AddPane(panel5, wx.aui.AuiPaneInfo().Top().CloseButton(False)
		#	.CaptionVisible(False))
		self.mgr.Update()
		self.Show()
#---------------------------------------------------------------------------------------------
		#Do all the bindings below

		# Bind MainRun
		self.redraw_timer = wx.Timer(self)
		self.redraw_timer_2 = wx.Timer(self)
		self.redraw_timer_3 = wx.Timer(self)


		self.Bind(wx.EVT_BUTTON, self.onMonitor, self.MainRun)
		# Bind Reheatself.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
		self.Bind(wx.EVT_TIMER, self.on_redraw_timer_2, self.redraw_timer_2)
		self.Bind(wx.EVT_TIMER, self.on_redraw_timer_3, self.redraw_timer_3)
		self.Bind(wx.EVT_BUTTON, self.onReheat, self.Reheat)
		# Bind Fce cool
		self.Bind(wx.EVT_BUTTON, self.onFurnaceCool, self.FCECoolBT)
		# Bind Cooling Process
		self.Bind(wx.EVT_BUTTON, self.CoolingProcess, self.Cooling)
		# Get temperature
		self.Bind(wx.EVT_BUTTON, self.onGetTemp, self.GetTemp)
		# Get Current Setpoint
		self.Bind(wx.EVT_BUTTON, self.onGetCSP, self.GetCSP)
		# Turn Solenoid on/off
		self.Bind(wx.EVT_BUTTON, self.onValveCon, self.ValveCon)
		# Switch furnace
		self.Bind(wx.EVT_BUTTON, self.onSwitchFCE, self.Furnace_switch)
		# Show Total Plot
		self.Bind(wx.EVT_BUTTON, self.onShowPlot, self.ShowPlot)
		# Get UPR
		#self.Bind(wx.EVT_BUTTON, self.onGetUPR, self.GetUPR)
		# Get DNR
		#self.Bind(wx.EVT_BUTTON, self.onGetDNR, self.GetDNR)
		# Bind timer 
		#self.Bind(wx.EVT_TIMER, self.on_redraw_timer, self.redraw_timer)
		# BIND SLIDER_EVENT
		self.Bind(wx.EVT_SLIDER, self.Updatesliders)
		# bind toolbar event
		self.Bind(wx.EVT_TOOL, self.OnQuit, tool6)
		self.Bind(wx.EVT_TOOL, self.OnSetting, tool5)
		# call popupmenu when right mouse button clicked
		self.sampleControlPanel.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		self.leftpane.Bind(wx.EVT_TEXT, self.UpdateText)
		self.leftpane.Bind(wx.EVT_BUTTON, self.setSampleLength, self.setSampleLengthButton)
		# Bind preview buttons
		self.sampleControlPanel.Bind(wx.EVT_BUTTON, self.onPreview1, self.preview1)
		self.sampleControlPanel.Bind(wx.EVT_BUTTON, self.onPreview2, self.preview2)
		self.sampleControlPanel.Bind(wx.EVT_BUTTON, self.onPreview3, self.preview3)
		self.sampleControlPanel.Bind(wx.EVT_BUTTON, self.onPreview4, self.preview4)
		# bind update button to onUpdate functions 
		self.notebook2.tabOne.Bind(wx.EVT_BUTTON, self.onUpdate1, self.notebook2.tabOne.updateButton)
		self.notebook2.tabTwo.Bind(wx.EVT_BUTTON, self.onUpdate2, self.notebook2.tabTwo.updateButton)
		self.notebook2.tabThree.Bind(wx.EVT_BUTTON, self.onUpdate3, self.notebook2.tabThree.upDate)
		# bind furnace temp preset
		self.Bind(wx.EVT_BUTTON, self.OnFce1_preset_BT, self.Fce1_preset_BT)
		self.Bind(wx.EVT_BUTTON, self.OnFce2_preset_BT, self.Fce2_preset_BT)
		# bind furnace HOLDING TIME
		self.Bind(wx.EVT_BUTTON, self.OnFce1_holdtime_BT, self.Fce1_holdtime_BT)
		self.Bind(wx.EVT_BUTTON, self.OnFce2_holdtime_BT, self.Fce2_holdtime_BT)

	def onShowPlot(self,event):
		filename1 = self.TestInfo.GetValue()+ ' Heating' + '.csv'
		filename2 = self.TestInfo.GetValue()+ ' Cooling' + '.csv'
		if self.Furnace2Lock == 1:
			filename3 = self.TestInfo.GetValue()+ ' Reheating' + '.csv'
			filename4 = self.TestInfo.GetValue()+ 'Furnace Cool' + '.csv'

		TargetFile1 = pd.read_csv(filename1) 
		ResultFile1 = TargetFile1[['time', 'thermocouple temp']]
		ResultFile1.columns = ['time', 'temp']
		ResultFile1 = pd.DataFrame(ResultFile1)

		rows = len(ResultFile1.axes[0]) - 1
		TimeInterval1 = ResultFile1.time[rows] + 4.5

		TargetFile2 = pd.read_csv(filename2) 
		ResultFile2 = pd.DataFrame(TargetFile2)
		ResultFile2[['time']] = ResultFile2[['time']].add(TimeInterval1)

		x = np.append(ResultFile1.time, ResultFile2.time)
		y = np.append(ResultFile1.temp, ResultFile2.temp)

		if self.Furnace2Lock == 1:

			TimeInterval2 = x[-1]

			TargetFile3 = pd.read_csv(filename3) 
			ResultFile3 = TargetFile3[['time', 'furnace 2 temp']]
			ResultFile3.columns = ['time', 'temp']
			ResultFile3 = pd.DataFrame(ResultFile3)

			#
			ResultFile3 = ResultFile3.irow(slice(-1, None))
			ResultFile3[['time']] = ResultFile3[['time']].add(TimeInterval2)

			x = np.append(x, ResultFile3.time)
			y = np.append(y, ResultFile3.temp)

			TimeInterval3 = x[-1] + 4.5

			TargetFile4 = pd.read_csv(filename4) 
			ResultFile4 = TargetFile4[['time', 'thermocouple temp']]
			ResultFile4.columns = ['time', 'temp']
			ResultFile4 = pd.DataFrame(ResultFile4)

			ResultFile4[['time']] = ResultFile4[['time']].add(TimeInterval3)

			x = np.append(x, ResultFile4.time)
			y = np.append(y, ResultFile4.temp)
		
		#x = np.around(x, decimals = 2)
		#y = np.around(y, decimals = 2)

		rawdata = np.array([x, y])
		rawdata = rawdata.T

		self.notebook.tabFive.axes.clear()
		self.notebook.tabFive.plot_data = self.notebook.tabFive.axes.plot(
			y, 
			linewidth=1,
			color='green',
			)[0]
		self.notebook.tabFive.plot_data.set_xdata(x)
		self.notebook.tabFive.plot_data.set_ydata(y)
		self.notebook.tabFive.axes.set_xlabel('time (s)')
		self.notebook.tabFive.axes.set_ylabel('Total temp history (C)', color='b')
		self.ymax5 = max(y) + max(y)*0.15
		self.ymin5 = 0
		self.xmax5 = max(x)*1.1
		self.xmin5 = 0
		self.notebook.tabFive.axes.set_ybound(lower=self.ymin5, upper=self.ymax5)
		self.notebook.tabFive.axes.set_xbound(lower=self.xmin5, upper=self.xmax5)
		self.notebook.tabFive.axes.grid(True)
		self.notebook.tabFive.canvas.draw()

		OutputFileName = self.TestInfo.GetValue() + ' total.csv'
		OutputFile = open(OutputFileName,'wb') 
		wr = csv.writer(OutputFile, dialect='excel')
		wr.writerow(["Time", "Temp"])
		wr.writerows(rawdata)
		print rawdata



	def onSwitchFCE(self, event):
		if self.Furnace_num == 1:
			self.StartBox.SetLabel('Furnace 2 Status')
			self.Furnace_num = 2
		else:
			self.StartBox.SetLabel('Furnace 1 Status')
			self.Furnace_num = 1

	def onReheat(self, event):
		hex_temp = getPV("02", ser)[7:11]
		temp = int(hex_temp,16)
		adc_temp = temp
		self.Furnace2_Temp[0] = temp
		self.Cooking_Timer_2 = time.time()
		self.Start_Time_2 = time.time()
		self.redraw_timer_2.Start(1000)
		self.lock = 2

	def onFurnaceCool(self,event):
		self.j3 = [0.0]
		self.j3.append(None)
		adc_temp = read3208(3)
		self.ADC_Temp[0] = adc_temp
		self.Cooking_Timer_3 = 0
		self.Start_Time_3 = time.time()
		GPIO.output(solenoid_valve_pin, GPIO.HIGH)
		self.redraw_timer_3.Start(500)

	# on_redraw_timer_3 is for furnace cooling process
	def on_redraw_timer_3(self, event):
		adc_temp = read3208(3)
		self.ADC_Temp[1] = adc_temp
		self.j3[1] =round((time.time() - self.Start_Time_3),2)
		self.notebook.tabFour.axes.plot(self.j3, self.ADC_Temp,color="red")
		self.j3[0] = self.j3[1]
		self.ADC_Temp[0] = self.ADC_Temp[1]
		#self.notebook.tabOne.ax2([self.xmin,self.xmax,self.ymin,self.ymax])
		self.notebook.tabFour.canvas.draw()
	
		"""
		msg = self.simulationDataPanel.grid.GridTableMessage(self,
			self.simulationDataPanel.GRIDTABLE_NOTIFY_ROWS_APPENDED,
			1)
		self.simulationDataPanel.GetView().ProgressTableMessage(msg)
		"""
		FCECoolData = [self.j3[1], adc_temp]
		FCECool.append(FCECoolData)
		if adc_temp - 260 < 0:
			GPIO.output(solenoid_valve_pin, GPIO.LOW)
			self.redraw_timer_3.Stop()
			print "Furnace Progress Finished"
			date = self.TestInfo.GetValue()+ 'Furnace Cool'
			filename = date+'.csv'
			resultFile = open(filename,'wb') 
			wr = csv.writer(resultFile, dialect='excel')
			wr.writerows(FCECool)
			GPIO.output(IR_sensor_pin, GPIO.LOW)

	# on_redraw_timer_2 is for Furnace two recording
	def on_redraw_timer_2(self, event):
		hex_temp = getPV("02", ser)[7:11]
		temp = int(hex_temp,16)
		adc_temp = read3208(0)
		self.Furnace2_Temp[1] = temp 
		self.ADC_Temp[1] = adc_temp

		self.j2[1] =round((time.time() - self.Start_Time_2),2)
		self.notebook.tabTwo.ax2.plot(self.j2,self.Furnace2_Temp,color="green")
		#self.notebook.tabTwo.ax2.plot(self.j2, self.ADC_Temp,color="red")
		self.Furnace2_Temp[0] = self.Furnace2_Temp[1]
		self.j2[0] = self.j2[1]
		self.ADC_Temp[0] = self.ADC_Temp[1]
		#self.notebook.tabOne.ax2([self.xmin,self.xmax,self.ymin,self.ymax])
		self.notebook.tabTwo.ax2.set_ybound(lower=self.ymin2, upper=self.ymax2)
		self.notebook.tabTwo.ax2.set_xbound(lower=self.xmin2, upper=self.xmax2)
		self.notebook.tabTwo.canvas.draw()
	
		"""
		msg = self.simulationDataPanel.grid.GridTableMessage(self,
			self.simulationDataPanel.GRIDTABLE_NOTIFY_ROWS_APPENDED,
			1)
		self.simulationDataPanel.GetView().ProgressTableMessage(msg)
		"""
		ReheatingData = [self.j2[1], temp, adc_temp]
		Reheating.append(ReheatingData)
		"""
		if abs(self.Fce2_preset.GetValue() - adc_temp) < 10.0 and self.lock == 2:
			self.Cooking_Timer_2 = time.time()
			print "start cooking timer 2"
			self.lock = 3
		"""
		if self.Cooking_Timer_2 != 0 and time.time() - self.Cooking_Timer_2 > self.IBHT_HoldingTime:
			self.redraw_timer_2.Stop()
			print "Reheating Progress Finished"
			self.furnace_cool_ready = 1
			date = self.TestInfo.GetValue()+ ' Reheating'
			filename = date+'.csv'
			resultFile = open(filename,'wb') 
			wr = csv.writer(resultFile, dialect='excel')
			wr.writerows(Reheating)
			self.onPreview3(self)
			time.sleep(4.5)
			self.onFurnaceCool(self)

	def OnFce1_preset_BT(self, event):
		if self.Fce1_preset.GetValue() != 0:
			setTemp(01, int((1.0+Overshoot)*self.Fce1_preset.GetValue()), ser)
		else:
			print "Furnace 1 temp has not been set yet."
	def OnFce2_preset_BT(self, event):
		if self.Fce2_preset.GetValue() != 0:
			setTemp(02, self.Fce2_preset.GetValue(), ser)
		else:
			print "Furnace 2 temp has not been set yet."
	def OnFce1_holdtime_BT(self, event):
		self.Peak_HoldingTime = self.Fce1_holdtime.GetValue() + 2.0

	def OnFce2_holdtime_BT(self, event):
		self.IBHT_HoldingTime = self.Fce2_holdtime.GetValue() 

	# Cooling process recording
	def CoolingProcess(self, event):
		if self.cooling_gap_timer != 0:
			self.cooling_gap = time.time() - self.cooling_gap_timer
			#GPIO.output(solenoid_valve_pin, GPIO.HIGH)
			print "start cooling process"
			# Thermocouple : fastRead(self.FC_SR, self.FC_ET, 0)
			# If use IR sensor: fastRead(self.FC_SR, self.FC_ET, 3)
			self.ADT_Time,self.ADT_Data = fastRead(self.FC_SR, self.FC_ET,self.FC_A1,3)# READ FROM ADC INPUT PIN 3
			print "Got Data"
			GPIO.output(solenoid_valve_pin, GPIO.LOW)
			# when using mcp3008(10 bit adc)
			#self.ADT_Volt = [round((elem*3.3)/float(1023),4) for elem in self.ADT_Data]
			#self.ADT_Temp = [(elem-1.25)/0.005 for elem in self.ADT_Volt]

			# when using mcp3208 with SI23
			"""
			self.ADT_Volt = [round((elem*3.3)/float(4095),4) for elem in self.ADT_Data]
			self.ADT_Temp = [(elem*1000/165.0-0.8)/(8.0/375.0) for elem in self.ADT_Volt]
			"""
			"""
			self.notebook.tabThree.axes.clear() 
			self.notebook.tabThree.plot_data = self.notebook.tabOne.axes.plot(
				self.ADT_Volt, 
				linewidth=1,
				color='purple',
				)[0]
			self.notebook.tabThree.plot_data.set_xdata(np.array(self.ADT_Time))
			self.notebook.tabThree.plot_data.set_ydata(np.array(self.ADT_Temp))

			self.notebook.tabThree.axes.set_xlabel('time (s)')
			self.notebook.tabThree.axes.set_ylabel('Sample temprature (C)', color='purple')
			self.adt_ymax = self.temps1[len(self.temps1) - 1]*1.15
			self.adt_ymin = 0
			self.adt_xmax = max(self.ADT_Time)*1.15
			self.adt_xmin = 0
			self.notebook.tabThree.axes.set_ybound(lower=self.adt_ymin, upper=self.adt_ymax)
			self.notebook.tabThree.axes.set_xbound(lower=self.adt_xmin, upper=self.adt_xmax)
			self.notebook.tabThree.axes.grid(True)
			self.notebook.tabThree.canvas.draw()
			"""

			RoundTime  = [round(elem, 3) for elem in self.ADT_Time]
			ADT_VOLT = [round((elem*4.96)/float(4096),4) for elem in self.ADT_Data]
			ADT_TEMP = [round(402.705314*elem-12.5,2) for elem in ADT_VOLT]
			x = np.array(RoundTime)
			y = np.array(ADT_TEMP)
			coolingrate = (y[-1]-y[0])/(x[-1]-x[0])
			
			ymax = max(y) + max(y)*0.15
			ymin = min(y) - min(y)*0.15
			xmax = max(x)
			xmin = 0
			self.notebook.tabThree.axes.clear()

			self.notebook.tabThree.plot_data = self.notebook.tabThree.axes.plot(
				y, 
				linewidth=1,
				color='green',
				)[0]
			self.notebook.tabThree.plot_data.set_xdata(x)
			self.notebook.tabThree.plot_data.set_ydata(y)
			self.notebook.tabThree.axes.set_ybound(lower=ymin, upper=ymax)
			self.notebook.tabThree.axes.set_xbound(lower=xmin, upper=xmax)
			self.notebook.tabThree.axes.set_xlabel('time (s)')
			self.notebook.tabThree.axes.set_ylabel('Cooling Process (C)', color='g')
			self.notebook.tabThree.axes.grid(True)
			self.notebook.tabThree.canvas.draw()
			#CoolingData = (x,y)
			rows = zip(RoundTime,ADT_TEMP)
			date = self.TestInfo.GetValue()+ ' Cooling'
			filename = date+'.csv'
			resultFile = open(filename,'wb') 
			wr = csv.writer(resultFile, dialect='excel')
			wr.writerow(Cooling)
			wr.writerows(rows)
			print "Gas Cooling finished."
			print "Cooling gap time is:"
			print self.cooling_gap
			print "Cooling Rate is:"
			print coolingrate
			if self.Furnace2Lock == 1:
				time.sleep(1)
				self.onPreview4(self)		
				time.sleep(3)
				self.onReheat(self)
		else:
			print "Sample not ready!"

	def onGetUPR(self,event):
		hex_temp = getUPR("01", ser)[7:11]
		temp = int(hex_temp,16)
		print "current Up Ramp:" 
		print temp, "C/min"

	def onGetDNR(self, event):
		hex_temp = getDNR("01", ser)[7:11]
		temp = int(hex_temp,16)
		print "current Down Ramp:" 
		print temp, "C/min"


	def onGetCSP(self, event):
		if self.Furnace_num == 1:
			hex_temp = getCSP("01", ser)[7:11]
			temp = int(hex_temp,16)
			print "current FCE 1 setpoint temp:" 
			print temp
		else:
			hex_temp = getCSP("02", ser)[7:11]
			temp = int(hex_temp,16)
			print "current FCE 2 setpoint temp:" 
			print temp


	def onGetTemp(self, event):
		if self.Furnace_num == 1:
			# this function is reading the temperature from the furnace built-in controller
			hex_temp = getPV("01", ser)[7:11]
			temp = int(hex_temp,16)
			print "current FCE 1 temp:" 
			print temp
		else:
			hex_temp = getPV("02", ser)[7:11]
			temp = int(hex_temp,16)
			print "current FCE 2 temp:" 
			print temp
		
		# read the tempertaure from the IR SENSOR,
		# the data is read out from the ADC MCP3008, which converts the anolog signals to digital
		"""
		temp = read3008(0)
		print "current temp:"
		print temp
		"""
	def onValveCon(self, event):
		if GPIO.input(solenoid_valve_pin) == 0:
			GPIO.output(solenoid_valve_pin, GPIO.HIGH)
			self.ValveCon.SetLabel('Turn Off')
			self.ValveBox.SetLabel('Solenoid Valve On')
			print "off"
		else:
			GPIO.output(solenoid_valve_pin, GPIO.LOW)
			self.ValveCon.SetLabel('Turn On')
			self.ValveBox.SetLabel('Solenoid Valve Off')
			print "on"

	# on_redraw_timer is for Furnace One recording
	def on_redraw_timer(self, event):
		hex_temp = getPV("01", ser)[7:11]
		temp = int(hex_temp, 16)
		adc_temp = read3208(4)
		diff = self.highest[0] - adc_temp
		# print "temp:"
		# print temp
		# print "Current set-temp:"TEM
		# print self.C_temps1[self.index]
		#print temp
		self.Furnace1_Temp[1] = temp 
		self.ADC_Temp[1] = adc_temp
		#if self.Furnace1_Temp[1]:
		#	self.Furnace1_Temp[0] = self.Furnace1_Temp[1]
		#self.Furnace1_Temp[1] = temp 
		self.j1[1] =round((time.time() - self.Start_Time),2)
		self.notebook.tabOne.ax2.plot(self.j1,self.Furnace1_Temp,color="green")
		self.notebook.tabOne.ax2.plot(self.j1, self.ADC_Temp,color="red")
		self.Furnace1_Temp[0] = self.Furnace1_Temp[1]
		self.j1[0] = self.j1[1]
		self.ADC_Temp[0] = self.ADC_Temp[1]
		#self.notebook.tabOne.ax2([self.xmin,self.xmax,self.ymin,self.ymax])
		self.notebook.tabOne.ax2.set_ybound(lower=self.ymin, upper=self.ymax)
		self.notebook.tabOne.ax2.set_xbound(lower=self.xmin, upper=self.xmax)
		self.notebook.tabOne.canvas.draw()
		self.simulationDataPanel.grid.AppendRows(numRows=1, updateLabels=True)

		if (time.time()-self.Start_Time) > self.drawingInterval[-1]-0.1:
			self.redraw_timer.Stop()
			self.lock = 2
			print "Progress 1 Finished"
			print "open lock"
			self.cooling_ready = 1
			print "cooling ready"
			date = self.TestInfo.GetValue()+ ' Heating'
			filename = date+'.csv'
			resultFile = open(filename,'wb') 
			wr = csv.writer(resultFile, dialect='excel')
			wr.writerows(Heating)
			self.onPreview3(self)
			GPIO.output(IR_sensor_pin, GPIO.HIGH)
			time.sleep(5)
			self.CoolingProcess(self)
	
		self.simulationDataPanel.grid.SetCellValue(self.GridIndex, 0, "%r" % (self.j1[1]))
		self.simulationDataPanel.grid.SetCellValue(self.GridIndex, 1, "%r" % (temp))
		self.simulationDataPanel.grid.SetCellValue(self.GridIndex, 2, "%r" % (self.C_temps1[self.index]))
		self.simulationDataPanel.grid.SetCellValue(self.GridIndex, 3, "%r" % (adc_temp))

		self.simulationDataPanel.grid.SetCellAlignment(self.GridIndex, 0, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
		self.simulationDataPanel.grid.SetCellAlignment(self.GridIndex, 1, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
		self.simulationDataPanel.grid.SetCellAlignment(self.GridIndex, 2, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
		self.simulationDataPanel.grid.SetCellAlignment(self.GridIndex, 3, wx.ALIGN_CENTER, wx.ALIGN_CENTER)
		"""
		msg = self.simulationDataPanel.grid.GridTableMessage(self,
			self.simulationDataPanel.GRIDTABLE_NOTIFY_ROWS_APPENDED,
			1)
		self.simulationDataPanel.GetView().ProgressTableMessage(msg)
		"""
		HeatingData = [self.j1[1], temp, self.C_temps1[self.index], adc_temp]
		Heating.append(HeatingData)

		self.GridIndex+=1
		#self.notebook.tabOne.canvas.draw()
		#if 0.95*self.highest[0] - adc_temp < 0 and self.lock == 0: # 880C
		#if 0.965*self.highest[0] - adc_temp < 0 and self.lock == 0: # 900C
		#if 0.935*self.highest[0] - adc_temp < 0 and self.lock == 0: # 800C
		#if 0.94*self.highest[0] - adc_temp < 0 and self.lock == 0: # 820C
		if 0.93*self.highest[0] - adc_temp < 0 and self.lock == 0: # 770C

			print "0.98*self.highest[0]:"
			print 0.98*self.highest[0]
			print "self.highest[0] - adc_temp"
			print self.highest[0] - adc_temp
			self.lock = 1
			setTemp(01, int(self.highest[0]), ser)
		if adc_temp > (self.highest[0]-2) and self.lock == 1 and self.lock_2 == 0:
			print "start 60sec timer"
			self.Cooking_Timer = time.time()
			self.lock = 2
			self.lock_2 = 1
			
			temp = temp - 4
			setTemp(01, temp, ser) # Under 900C
			print "setting furnace to lower temp"
			print temp
			print "highest"
			print self.highest[0]
			#setTemp(01, int(self.highest[0]*0.95), ser) #900C
			
# holdinng time
		if self.Cooking_Timer != 0 and time.time() - self.Cooking_Timer > self.Peak_HoldingTime:
			self.redraw_timer.Stop()
			print "Progress 1 Finished"
			print "open lock"
			self.lock = 2
			self.cooling_ready = 1
			date = self.TestInfo.GetValue()+ ' Heating'
			filename = date+'.csv'
			resultFile = open(filename,'wb') 
			wr = csv.writer(resultFile, dialect='excel')
			wr.writerows(Heating)
			self.onPreview3(self)
			GPIO.output(IR_sensor_pin, GPIO.HIGH)
			time.sleep(4.5)
			self.CoolingProcess(self)


		if temp == self.C_temps1[self.index] and self.C_temps1[self.index]!=self.C_temps1[self.index+1]:
			if self.C_temps1[self.index+1]:
				self.index += 1
				if self.index<len(self.C_temps1) and self.C_temps1[self.index]>self.C_temps1[self.index-1]:
					UD = 1
					ramp = int((self.C_temps1[self.index] - temp) / (self.C_interval1[self.index]/60))
					setRamp(01,ramp,UD,ser)
					time.sleep(0.2)
					setTemp(01, self.C_temps1[self.index], ser)
				elif self.index<len(self.C_temps1) and self.C_temps1[self.index]<self.C_temps1[self.index-1]:
					UD = -1
					ramp = int((temp - self.C_temps1[self.index]) / (self.C_interval1[self.index]/60))
					setRamp(01,ramp,UD,ser)
					time.sleep(0.2)
					setTemp(01, self.C_temps1[self.index], ser)
			elif self.C_temps1[self.index+1] == None and (time.time()-self.Start_Time) - self.drawingInterval[-1] > 0:
				self.redraw_timer.Stop()
				print "Progress 1 Finished"
				self.CoolingProcess()
				#RunStepper(self.position3, self.speed, 3)


		elif temp == self.C_temps1[self.index] and self.C_temps1[self.index]==self.C_temps1[self.index+1]:
			if (time.time()-self.Start_Time) < self.drawingInterval[self.index+2] and self.flag == 0:
				self.flag = 1
				setRamp(01,0,1,ser)
				setRamp(01,0,-1,ser)
				setTemp(01, self.C_temps1[self.index], ser)
			elif (time.time()-self.Start_Time) > self.drawingInterval[self.index+2]:
				print (time.time()-self.Start_Time) - self.drawingInterval[self.index+2]
				self.flag = 0
				self.index += 2
				if self.index<len(self.C_temps1) and self.C_temps1[self.index]>self.C_temps1[self.index-1]\
					and (temp - self.C_temps1[self.index])!=0:
					UD = 1
					ramp = int((self.C_temps1[self.index] - temp) / (self.C_interval1[self.index]/60))
					setRamp(01,ramp,UD,ser)
					time.sleep(0.2)
					setTemp(01, self.C_temps1[self.index], ser)
				elif self.index<len(self.C_temps1) and self.C_temps1[self.index]<self.C_temps1[self.index-1]\
					and (temp - self.C_temps1[self.index])!=0:
					UD = -1
					ramp = int((temp - self.C_temps1[self.index]) / (self.C_interval1[self.index]/60))
					setRamp(01,ramp,UD,ser)
					time.sleep(0.2)
					setTemp(01, self.C_temps1[self.index], ser)
				elif (temp - self.C_temps1[self.index])==0:
					ramp = int(0)
					setRamp(01,ramp,1,ser)
					time.sleep(0.2)
					setTemp(01, temp, ser)
					self.redraw_timer.Stop()
					print "Progress 1 Finished"
					self.CoolingProcess()
					#RunStepper(self.position3, self.speed, 3)


		
		elif self.index == (len(self.C_temps1)-1) and adc_temp - self.highest[0] > 0:
			self.lock = 2
			self.redraw_timer.Stop()
			print "Progress 1 Finished"
			print "open lock"
			self.cooling_ready = 1
			date = self.TestInfo.GetValue()+ ' Heating'
			filename = date+'.csv'
			resultFile = open(filename,'wb') 
			wr = csv.writer(resultFile, dialect='excel')
			wr.writerows(Heating)
			#self.CoolingProcess()
			#RunStepper(self.position3, self.speed, 3)

	def onMonitor(self, event):
		"""
		if self.RunFlag== 0:
			self.RunFlag = 1
			RunStepper(self.position2, self.speed, 2)
		"""
		self.lock_2 = 0
		self.lock = 0
		self.Start_Time = time.time()
		self.Cooking_Timer = 0
		self.index = 0
		self.GridIndex = 0
		#hex_temp = getPV("01", ser)[7:11]
		#temp = int(hex_temp,16)
		temp = self.temps1[0]
		print "temp:" 
		print temp
		
		if temp < self.C_temps1[self.index]:
			UD = 1
			ramp = round((self.C_temps1[self.index] - temp) / (self.C_interval1[self.index]/60.0))
			print "ramp"
			print (self.C_interval1[self.index]/60)
			ramp = int(ramp)
			print UD,ramp
			setRamp(01,ramp,UD,ser)
			time.sleep(1)
			setTemp(01, self.C_temps1[self.index], ser) 
			print "sent"
			
		elif temp > self.C_temps1[self.index]:
			UD = -1
			ramp = round((temp - self.C_temps1[self.index]) / (self.C_interval1[self.index]/60.0))
			ramp = int(ramp)
			print UD,ramp
			setRamp(01,ramp,UD,ser)
			time.sleep(1)
			setTemp(01, self.C_temps1[self.index], ser)
			print "sent"
		self.onPreview2(self)
		time.sleep(10)
		print "using mcp3208 channel 4"
		print "temp:"
		print read3208(4)
		self.redraw_timer.Start(1000)
		#print getPV(01, ser)[7:11]
		#temp = int(hex_temp,16)
		#print self.Start_Time
		#print self.Start_Time
		#print "start..."


	def onUpdate1(self, event):
		self.temps1 = self.notebook2.tabOne.setpoint
		self.Furnace1_Temp = [self.temps1[0]]
		self.Furnace1_Temp.append(None)
		self.j1 = [0.0]
		self.j1.append(None)
		self.ADC_Temp = [read3208(0)]
		self.ADC_Temp.append(None)
		self.interval1 = self.notebook2.tabOne.setTime
		self.temps1 = [x for x in self.temps1 if x is not None]
		# highest is the biggest number in temps1
		# will use this number to draw a dash line later
		self.temps1, self.highest, self.hight_pos = list_biggest(self.temps1, 1.0 + Overshoot)
		# C_temps1 and C_interval1 stands for communicational temps and intervals
		self.C_temps1 = self.temps1[1:]
		self.C_temps1 = [int(x) for x in self.C_temps1]
		print self.C_temps1
		self.C_interval1 = self.interval1[1:]
		self.interval1 = [x for x in self.interval1 if x is not None]
		self.notebook.tabOne.axes.clear()
		#self.notebook.tabOne.ax2.clear() 
		#self.notebook.tabOne.ax3.clear() 

		self.notebook.tabOne.plot_data = self.notebook.tabOne.axes.plot(
			self.temps1, 
			linewidth=1,
			color='blue',
			)[0]

		self.drawingInterval = newlist(self.interval1)
		self.notebook.tabOne.plot_data.set_xdata(np.array(self.drawingInterval))
		self.notebook.tabOne.plot_data.set_ydata(np.array(self.temps1))
		
		self.notebook.tabOne.plot_data3 = self.notebook.tabOne.ax3.plot(
			self.temps1, 
			linewidth=1,   
			dashes=[8, 4, 2, 4, 2, 4],
			color='purple'
			)[0]
		self.notebook.tabOne.plot_data3.set_xdata(np.array(self.drawingInterval))
		self.highest = [self.highest[0]]*len(self.drawingInterval)
		self.notebook.tabOne.plot_data3.set_ydata(np.array(self.highest))
		
		#self.notebook.tabOne.axes.set_xlabel('time (s)')
		#self.notebook.tabOne.axes.set_ylabel('Preset temprature (C)', color='b')
		self.notebook.tabOne.ax3.set_xlabel('time (s)')
		self.notebook.tabOne.ax3.set_ylabel('Preset temprature (C)', color='b')
		self.ymax = max(self.temps1)*1.15
		self.ymin = 0
		self.xmax = max(self.drawingInterval)
		self.xmin = 0
		self.notebook.tabOne.axes.set_ybound(lower=self.ymin, upper=self.ymax)
		self.notebook.tabOne.axes.set_xbound(lower=self.xmin, upper=self.xmax)
		self.notebook.tabOne.ax3.set_ybound(lower=self.ymin, upper=self.ymax)

		"""
		for i in range(len(self.data1)-1):
            self.datay.append(max(self.data1))
        self.plot_data3.set_xdata(np.arange(len(self.data1)))
        self.plot_data3.set_ydata(np.array(self.datay))
        """

		self.notebook.tabOne.axes.grid(True)
		#self.notebook.tabOne.ax3.grid(True)
		self.notebook.tabOne.canvas.draw()
		#print setTemp(01, self.temps1)
		#print setInterval(01, self.interval1)

	def onUpdate2(self, event):
		self.temps2 = self.notebook2.tabTwo.setpoint
		self.Furnace2_Temp = [self.temps2[0]]
		self.Furnace2_Temp.append(None)
		self.j2 = [0.0]
		self.j2.append(None)
		self.ADC_Temp = [self.temps2[-1]]
		self.ADC_Temp.append(None)
		self.interval2 = self.notebook2.tabTwo.setTime
		self.temps2 = [x for x in self.temps2 if x is not None]
		self.temps2, self.highest2, self.hight_pos2 = list_biggest(self.temps2, 1.0)
		self.C_temps2 = self.temps2[1:]
		self.C_temps2 = [int(x) for x in self.C_temps2]
		self.C_interval2 = self.interval2[1:]
		self.interval2 = [x for x in self.interval2 if x is not None]

		self.notebook.tabTwo.axes.clear()
		#self.notebook.tabTwo.ax2.clear()
		#self.notebook.tabTwo.ax3.clear()
		self.notebook.tabTwo.plot_data = self.notebook.tabTwo.axes.plot(
			self.temps2, 
			linewidth=1,
			color='blue',
			)[0]
		self.drawingInterval2 = newlist(self.interval2)
		self.notebook.tabTwo.plot_data.set_xdata(np.array(self.drawingInterval2))
		self.notebook.tabTwo.plot_data.set_ydata(np.array(self.temps2))

		self.notebook.tabTwo.plot_data3 = self.notebook.tabTwo.ax3.plot(
			self.temps2,
			linewidth=1,
			dashes=[8, 4, 2, 4, 2, 4],
			color='purple'
			)[0]

		self.notebook.tabTwo.plot_data3.set_xdata(np.array(self.drawingInterval2))
		self.highest2 = [self.highest2[0]]*len(self.drawingInterval2)
		self.notebook.tabTwo.plot_data3.set_ydata(np.array(self.highest2))

		self.notebook.tabTwo.axes.set_xlabel('time (s)')
		self.notebook.tabTwo.axes.set_ylabel('Preset temprature (C)', color='b')
		self.ymax2 = max(max(self.temps1),max(self.temps2)) + max(self.temps2)*0.15
		self.ymin2 = 0
		self.xmax2 = max(self.drawingInterval2)
		self.xmin2 = 0
		self.notebook.tabTwo.axes.set_ybound(lower=self.ymin2, upper=self.ymax2)
		self.notebook.tabTwo.axes.set_xbound(lower=self.xmin2, upper=self.xmax2)
		self.notebook.tabTwo.ax3.set_ybound(lower=self.ymin2, upper=self.ymax2)

		self.notebook.tabTwo.axes.grid(True)
		self.notebook.tabTwo.canvas.draw()
		self.Furnace2Lock = 1

	def onUpdate3(self, event):
		self.notebook2.tabThree.ST_Input.SetLabel(str(self.temps1[len(self.temps1) - 1]))
		# store the sampling rate
		self.FC_ET = self.notebook2.tabThree.ET.GetValue()
		# store the end temp
		self.FC_SR = self.notebook2.tabThree.SR.GetValue()
		# store the A1 temp
		if self.notebook2.tabThree.HoldValve.GetValue():
			self.FC_A1 = self.notebook2.tabThree.A1_Temp.GetValue()
			print "Hold to A1 @: ", self.FC_A1, 'C'
		else: 
			print "No Hold, direct cool to End Temp from ", self.temps1[len(self.temps1) - 1], 'C'
			self.FC_A1 = self.temps1[len(self.temps1) - 1]

	def onFocus(self, event):
		self.sampleControlPanel.SetFocus()

	# ACTION for preview 1 button press
	def onPreview1(self, event):
		self.position1 = self.positionSlider1.GetValue()
		self.speed = self.sms.GetValue()
		# convert distance unit mm to stepper motor's microsteps
		# 1 stepper motor step = 1.8 degree,
		# 16 micro-steps = 1 step | 1 micro-step = 0.1125 degrees
		RunStepper(self.position1, self.speed, self.sl.GetValue(),1)
		"""
		time.sleep(15)
		Distance = '1000' + 'Dis'
		cmd = Distance + Speed + direct
		communication_send(addr, "stm", cmd)
		"""

	# ACTION for preview 2 button press
	def onPreview2(self, event):
		self.position2 = self.positionSlider2.GetValue()
		self.speed = self.sms.GetValue()
		# convert distance unit mm to stepper motor's microsteps
		# 1 stepper motor step equals 1.8 degree,
		# 16 micro-steps equals 1 step
		RunStepper(self.position2, self.speed, self.sl.GetValue(),2)
		"""
		time.sleep(15)
		Distance = '1000' + 'Dis'
		cmd = Distance + Speed + direct
		communication_send(addr, "stm", cmd)
		"""

	# ACTION  for preview 3 button press
	def onPreview3(self, event):
		self.position3 = self.positionSlider3.GetValue()
		self.speed = self.sms.GetValue()
		# convert distance unit mm to stepper motor's microsteps
		# 1 stepper motor step equals 1.8 degree,
		# 16 micro-steps equals 1 step
		RunStepper(self.position3, self.speed, self.sl.GetValue(), 3)
		if self.cooling_ready == 1:
			self.cooling_gap_timer = time.time()
		print "self.cooling_gap_timer"
		"""
		time.sleep(15)
		Distance = '1000' + 'Dis'
		cmd = Distance + Speed + direct
		communication_send(addr, "stm", cmd)
		"""

	# ACTION for preview 4 button press
	def onPreview4(self, event):
		self.position4 = self.positionSlider4.GetValue()
		self.speed = self.sms.GetValue()
		# convert distance unit mm to stepper motor's microsteps
		# 1 stepper motor step equals 1.8 degree,
		# 16 micro-steps equals 1 step
		RunStepper(self.position4, self.speed, self.sl.GetValue(), 4)
		"""
		time.sleep(15)
		Distance = '1000' + 'Dis'
		cmd = Distance + Speed + direct
		communication_send(addr, "stm", cmd)
		"""

	def setSampleLength(self, event):
		self.SampleLength = self.sl.GetValue()
		self.positionSlider1.SetMax(354 - self.SampleLength)
		self.positionSlider2.SetMax(410 - self.SampleLength)
		self.positionSlider3.SetMax(330 - self.SampleLength)
		self.positionSlider4.SetMax(750 - self.SampleLength)

	# GUI UPDATE slider display
	def Updatesliders(self, e):
		self.setpoint1 = self.positionSlider1.GetValue()
		self.ssp1.SetValue(self.setpoint1)
		self.setpoint2 = self.positionSlider2.GetValue()
		self.ssp2.SetValue(self.setpoint2)
		self.setpoint3 = self.positionSlider3.GetValue()
		self.ssp3.SetValue(self.setpoint3)
		self.setpoint4 = self.positionSlider4.GetValue()
		self.ssp4.SetValue(self.setpoint4)

	# GUI UPDATE text display
	def UpdateText(self, event):
		#make sure the right text boxes are selected
		if (event.GetId()<=103 and event.GetId()>=100):
			self.setpoint1 = self.ssp1.GetValue()
			self.positionSlider1.SetValue(self.setpoint1)
			self.setpoint2 = self.ssp2.GetValue()
			self.positionSlider2.SetValue(self.setpoint2)
			self.setpoint3 = self.ssp3.GetValue()
			self.positionSlider3.SetValue(self.setpoint3)
			self.setpoint4 = self.ssp4.GetValue()
			self.positionSlider4.SetValue(self.setpoint4)

	def OnQuit(self, e):
		self.Close()

	def OnSetting(self, e):
		Setting = STM_T()
		Setting.Show()

	def OnRightDown(self, e):
		self.PopupMenu(MyPopupMenu(self.sampleControlPanel), e.GetPosition())

class MyPopupMenu(wx.Menu): # popup menu for Example frame
    
    def __init__(self, parent):
        super(MyPopupMenu, self).__init__()
        
        self.parent = parent

        mmi = wx.MenuItem(self, wx.NewId(), 'Minimize') # minimize frame
        self.AppendItem(mmi) # append mmi to popupmenu
        self.Bind(wx.EVT_MENU, self.OnMinimize, mmi) # bind OnMinimize function to mm

        cmi = wx.MenuItem(self, wx.NewId(), 'Close') # close frame
        self.AppendItem(cmi) # append cmi to popupmenu
        self.Bind(wx.EVT_MENU, self.OnClose, cmi) # bind OnClose Function to cmi

    def OnMinimize(self, e):
        self.parent.Iconize()

    def OnClose(self, e):
        self.parent.Close()

def main():
	test_thread = threading.Thread(target = solenoid_thread)
	test_thread.start()
	ex = wx.App()
	MainFrame(None, "CAL Simulator")
	ex.MainLoop()

if __name__=='__main__':
	main()


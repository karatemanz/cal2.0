import wx
import os
import time
import math
import RPi.GPIO as GPIO

import util as util
from RPI_I2C_ARDUINO import *

# Initialize Motor Control Variables // 120 is standard simulation speed
addr = 0x04
motorSpeed = 60

# Initialize stages for GATE CONTROL
endStage = 4
startStage=4
# -----------------------------------------------
# Sample lengths for simulation are in milimeters
# -----------------------------------------------
## Load A.T.M. -> approx. 1 inch from top (~25mm)
# -----------------------------------------------
# 4   inch -> 100
# 7.5 inch -> 190
# 8   inch -> 200
# -----------------------------------------------
# convert distance unit mm to stepper motor's microsteps
# 1 stepper motor step equals 1.8 degree,
# 16 micro-steps equals 1 step

# Initialize gate solenoid pin
solenoidPin1 = 26
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
GPIO.setup(solenoidPin1, GPIO.OUT)
GPIO.output(solenoidPin1, GPIO.LOW)

def RelativeStepper(speed, sampleLength, position_num):
	global endStage
	global startStage
	
	startStage = endStage
	
	sampleLength = int(sampleLength)
	
	if position_num == util.Furnace_1:
		x = 1090
		endStage = util.Furnace_1
	elif position_num == util.Cool:
		x = 700
		endStage = util.Cool
	elif position_num == util.Furnace_2:
		x = 270
		endStage = util.Furnace_2
	elif position_num == util.Load:
		x = 250 - (3*sampleLength)/2
		endStage = util.Load
	
	# 110.3 is the diameter of the motor wheel	
	distance_ = int(float(x + sampleLength/2)*(3200/(math.pi*110.4)))
	distance_ = str(distance_)
	Distance = distance_ + 'Dis'
	  
	# convert speed unit rpm to stepper motor's microsteps/sec
	speed_ = int(float(speed)*(3200/60))
	speed_ = str(speed_)
	Speed = speed_ + 'Spd'
	 
	Position = str(position_num) + 'P'
	
	Direct = '1' + 'E'# 'E' stands for end.
	
	cmd = Distance + Speed + Position + Direct
	communication_send(addr, "stm", cmd)
	getStatus(addr)
	
	return startStage

def LoadStepper(speed, sampleLength):
	global endStage
	global startStage
	
	startStage = 4
	
	sampleLength = int(sampleLength)
	
	# 110.3 is the diameter of the motor wheel	
	distance_ = int(float(250 - sampleLength)*(3200/(math.pi*110.4)))
	distance_ = str(distance_)
	Distance = distance_ + 'Dis'
	  
	# convert speed unit rpm to stepper motor's microsteps/sec
	speed_ = int(float(speed)*(3200/60))
	speed_ = str(speed_)
	Speed = speed_ + 'Spd'
	 
	position_num = 4 
	Position = str(position_num) + 'P'
	
	Direct = '1' + 'E'# 'E' stands for end.
	
	cmd = Distance + Speed + Position + Direct
	communication_send(addr, "stm", cmd)
	getStatus(addr)
	
	return startStage	
	
class STM_T(wx.Frame): # STM_T is a frame for stepper motor testing

	def __init__(self):
		
		self.gate_position = 0
		distance=''
		speed=''
		length=''
		
		wx.Frame.__init__(self,None, title= 'Stepper Motor Test', size=(600, 500))
		self.Centre()
		self.statusbar = self.CreateStatusBar()
		self.panel2 = panel2 = wx.Panel(self)

		sizer = wx.GridBagSizer(5,4)

		text1 = wx.StaticText(panel2, label='Stepper Motor Testing')

		sizer.Add(text1, pos=(0, 0), flag=wx.TOP|wx.LEFT|wx.BOTTOM, border=15)

		imagesPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))

		icon = wx.StaticBitmap(panel2, bitmap=wx.Bitmap(os.path.join(imagesPath, 'images/stm2.png')))
		sizer.Add(icon, pos=(0, 3), flag=wx.TOP|wx.RIGHT, border=7)
		line = wx.StaticLine(panel2)
		sizer.Add(line, pos=(1, 0), span=(1, 5), flag=wx.EXPAND|wx.BOTTOM, border=10)

		text2 = wx.StaticText(panel2, label='Distance')
		sizer.Add(text2, pos=(2, 0), flag=wx.LEFT, border=10)

		unit1 = wx.StaticText(panel2, label='mm')
		sizer.Add(unit1, pos=(2, 3), flag=wx.LEFT, border=7)

		unit2 = wx.StaticText(panel2, label='rpm')
		sizer.Add(unit2, pos=(3, 3), flag=wx.LEFT|wx.TOP, border=7)
		
		unit3 = wx.StaticText(panel2, label='mm')
		sizer.Add(unit3, pos=(5, 3), flag=wx.LEFT, border=7)
		200
		self.tc1= tc1 = wx.TextCtrl(panel2,value=distance)
		sizer.Add(tc1, pos=(2, 1), span=(1, 2), flag=wx.TOP|wx.EXPAND)

		text3 = wx.StaticText(panel2, label='Speed')
		sizer.Add(text3, pos=(3, 0), flag=wx.LEFT|wx.TOP, border=10)

		self.tc2 = tc2 = wx.TextCtrl(panel2, value=speed)
		sizer.Add(tc2, pos=(3, 1), span=(1, 2), flag=wx.TOP|wx.EXPAND, border=5)
			
		text4 = wx.StaticText(panel2, label='Direction')
		sizer.Add(text4, pos=(4, 0), flag=wx.TOP|wx.LEFT, border=10)

		self.combo3 = combo3 = wx.ComboBox(panel2, style=wx.CB_DROPDOWN|wx.CB_READONLY, choices=['Clockwise','Counter Clockwise'])
		combo3.SetSelection(0)
		sizer.Add(combo3, pos=(4, 1), span=(1, 3), flag=wx.TOP|wx.EXPAND, border=5)

		textLength = textLength = wx.StaticText(panel2, label='Length')
		sizer.Add(textLength, pos=(5, 0), flag=wx.LEFT|wx.TOP, border=10)

		self.tl = tl = wx.TextCtrl(panel2, value=length)
		sizer.Add(tl, pos=(5, 1), span=(1, 2), flag=wx.TOP|wx.EXPAND, border=5)

		button1 = wx.Button(panel2, label='Position Demonstration')
		sizer.Add(button1, pos=(7, 3), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnPD, button1)

		button6 = wx.BitmapButton(panel2, 
		bitmap=wx.Bitmap(os.path.join(imagesPath, 'images/back.png')))
		sizer.Add(button6, pos=(8, 0), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnQuit, button6)

		gateButton = wx.Button(panel2, label='GATE')
		sizer.Add(gateButton, pos=(8, 1), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnGate, gateButton)

		button4 = wx.Button(panel2, label='RUN')
		sizer.Add(button4, pos=(8, 2), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnRun, button4)

		button5 = wx.Button(panel2, label='QUIT')
		sizer.Add(button5, pos=(8, 3), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnStop, button5)
		
		loadButton = wx.Button(panel2, label='LOAD')
		sizer.Add(loadButton, pos=(9, 0), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnLoad, loadButton)
		
		f2Button = wx.Button(panel2, label='F2')
		sizer.Add(f2Button, pos=(9, 1), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnFurnace2, f2Button)
		
		coolButton = wx.Button(panel2, label='COOL')
		sizer.Add(coolButton, pos=(9, 2), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnCool, coolButton)
		
		f1Button = wx.Button(panel2, label='F1')
		sizer.Add(f1Button, pos=(9, 3), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnFurnace1, f1Button)
		
		ir1Button = wx.Button(panel2, label='IR-F1')
		sizer.Add(ir1Button, pos=(10, 0), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnIRFurnace1, ir1Button)
		
		ir2Button = wx.Button(panel2, label='IR-COOL')
		sizer.Add(ir2Button, pos=(10, 1), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnIRCool, ir2Button)
		
		ir3Button = wx.Button(panel2, label='IR-F2')
		sizer.Add(ir3Button, pos=(10, 2), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnIRFurnace2, ir3Button)
		
		stageButton = wx.Button(panel2, label='STAGE')
		sizer.Add(stageButton, pos=(10, 3), span=(1, 1), flag=wx.LEFT, border=10)
		panel2.Bind(wx.EVT_BUTTON, self.OnStage, stageButton)

		sizer.AddGrowableCol(2)

		panel2.SetSizer(sizer)


	# Run Position Demonstration
	def OnPD(self, event):
		
		global startStage
		sampleLength = self.tl.GetValue()
			
		if sampleLength == '':
			sampleLength = 200
		
		print("Presentation Demo Event")
		
		#Stepper(position, speed, SampleLength, position_num)
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Load)
		self.statusbar.SetStatusText("going to loading position")
		print "Load"
		time.sleep(5)

		startStage = RelativeStepper(motorSpeed, sampleLength, util.Cool)
		self.statusbar.SetStatusText("going into cooling position")
		print "Cool (Start State)"
		time.sleep(10)
		
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Furnace_1)
		self.statusbar.SetStatusText("going into first furnace")
		print "Furnace 1 (First Heat Treatment)"
		time.sleep(5)
		
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Cool)
		self.statusbar.SetStatusText("going into cooling position")
		print "Cool (Cooling Stage)"
		time.sleep(10)

		startStage = RelativeStepper(motorSpeed, sampleLength, util.Furnace_2)
		self.statusbar.SetStatusText("going into 2nd furnace to reheat")
		print "Furnace 2 (Second Heat Treatment)"
		time.sleep(5)

		startStage = RelativeStepper(motorSpeed, sampleLength, util.Load)
		self.statusbar.SetStatusText("back to loading position")
		print "Unloading"
		

	# Quit Popup
	def OnQuit(self, event):
		self.Close()

	# Move Gate: Slightly Buggy Due To Gate Bounce
	def OnGate(self, event):
		
		if self.gate_position == 0:
			self.gate_position = 1
			print "gate open"
			GPIO.output(solenoidPin1, GPIO.HIGH)
			time.sleep(1.0)
						
		elif self.gate_position == 1:
			self.gate_position = 0
			print "gate close"
			GPIO.output(solenoidPin1, GPIO.LOW)
			time.sleep(1.0)			

	# Running The Stepper Motor Without Sample Constraints
	def OnRun(self, event):
		
		distance_ = int(float(self.tc1.GetValue())*(3200/(math.pi*70)))
		distance_ = str(distance_)
		Distance = distance_ + 'Dis'
		  
		speed_ = int(float(self.tc2.GetValue())*(3200/60))
		speed_ = str(speed_)
		Speed = speed_ + 'Spd'
		 
		Direction = self.combo3.GetValue()
		direct = ''
		
		if Direction == 'Clockwise':
			Direct = '0' + 'E'  # 'E' stands for end.
		elif Direction == 'Counter Clockwise':
			Direct = '1' + 'E'

		cmd = Distance + Speed + Direct
		communication_send(addr, "stm", cmd)
		received = getStatus(addr)
		print received
		
	# Run The Stepper Motor To The Stage| Simulation Sample Staging
	def OnStage(self, event):
			
		# This is used to move the sample into the correct position before running a simulation
		# Compensates for the drop of the sample when the simulator is turned off
		# Use this for preparing a sample for simulation
		# Should be automatically called 5 seconds after CAL has been started 
			
		sampleLength = self.tl.GetValue()
			
		if sampleLength == '':
			sampleLength = 200
		
		print "sampleLength = %r" %sampleLength
		
		startStage = LoadStepper(motorSpeed, sampleLength)
		self.statusbar.SetStatusText("going to sample staging position")
		print "Load"
		time.sleep(2)	
			
	# Run The Stepper Motor To Load Position| Simulation Ending Stage
	def OnLoad(self, event):
		
		sampleLength = self.tl.GetValue()
			
		if sampleLength == '':
			sampleLength = 200
		
		print "sampleLength = %r" %sampleLength
		
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Load)
		self.statusbar.SetStatusText("going to loading position")
		print "Load"
		time.sleep(2)
	
	# Run The Stepper Motor To The Second Furnace Position (Lower Furnace)| Simulation Reheat Stage
	def OnFurnace2(self, event):
		
		sampleLength = sampleLength = self.tl.GetValue()
		
		if sampleLength == '':
			sampleLength = 200
		
		print "sampleLength = %r" %sampleLength
		
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Furnace_2)
		self.statusbar.SetStatusText("going to furnace 2's position")
		print "Furnace 2"
		time.sleep(2)

	# Run The Stepper Motor To The Cooling Postion| Simulation Cooling Stage
	def OnCool(self, event):
		
		sampleLength = sampleLength = self.tl.GetValue()
		
		if sampleLength == '':
			sampleLength = 200
		
		print "sampleLength = %r" %sampleLength
		
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Cool)
		self.statusbar.SetStatusText("going to cooling position")
		print "Cooling"
		time.sleep(2)
		
	# Run The Stepper Motor To The First Furnace Position (Top Furnace)| Simulation Initial Heating Stage
	def OnFurnace1(self, event):
		
		sampleLength = sampleLength = self.tl.GetValue()
		
		if sampleLength == '':
			sampleLength = 200
		
		print "sampleLength = %r" %sampleLength
		
		startStage = RelativeStepper(motorSpeed, sampleLength, util.Furnace_1)
		self.statusbar.SetStatusText("going to furnace 1's position")
		print "Furnace 1"
		time.sleep(2)
		
	# Read The IR Sensor Of The First Furnace	
	def OnIRFurnace1(self, event):
		print "read furnace 1 sample temp"
		temp = util.read3208(util.F1Channel)
		
		print "TEMP = %r" %temp
				
	# Read The IR Sensor Of The Cooling Area			
	def OnIRCool(self, event):
		print "read cooling sample temp"
		temp = util.read3208(util.CoolChannel)
	
		print "TEMP = %r" %temp
		
	# Read The IR Sensor Of The Second Furnace	
	def OnIRFurnace2(self, event):
		print "read furnace2 sample temp"
		temp = util.read3208(util.F2Channel)
	
		print "TEMP = %r" %temp				
				
	# Stop
	def OnStop(self, event):
		self.Close()

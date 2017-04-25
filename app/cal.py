#---------------------------------------------------------------------------------------------------------
# CAL Simulator Control Package
#
#	Contributors from this point:
#		Andrew Zundel -> adz13@pitt.edu    // Please contact if you need any information about code and process
#		Daniel Figula -> daf84@pitt.edu	   // Please contact if you need any information about circuitry and process
#		Kaitlyn Carey -> kac241@pitt.edu
#
#	Packages of Simulators Interest
#		1) Gate 			-> solenoid_thread_test.py
#		2) Temperature		-> FastRead.py for IR sensors AND menus7.py contains Furnace Communication functionality
#		3) Positioning      -> STM.py
#
#-----------------------------------------------------------------------------------------------------------

import time
import wx
import os
import serial
import spidev
import csv
import threading
import pandas as pd
import numbers
from Tkinter import Tk
from tkFileDialog import askopenfilename
import RPi.GPIO as GPIO
import wx.aui,wx.lib.intctrl, wx.lib.scrolledpanel
import wx.lib.agw.flatnotebook as fnb
import numpy as np
from numpy import arange, sin, pi
import matplotlib
matplotlib.interactive( True )
matplotlib.use('WXAgg')
from pylab import *
import matplotlib.pyplot as plt
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.backends.backend_wx import NavigationToolbar2Wx
from matplotlib.figure import Figure

import heatPanel
import coolPanel
import reheatPanel
import totalPanel
import simPanel
import LiveFurnace as furn
import LiveIR as ir
import gate_thread as gt
import util
import furnace_control as fc
import summary as sim

pad = 2

# Initialize control, logic, and data variables
Overshoot = 0.0 			# small sample
Vref = 4.96*(653.7/330.0)
counter = 0

# Initialize GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

# Cooling valves solenoid pin set-up and init
coolingValvePin = 13
GPIO.setup(coolingValvePin, GPIO.OUT)
GPIO.output(coolingValvePin, GPIO.LOW)

# IR Sensor pin set-up and init
IR_sensor_pin = 19
GPIO.setup(IR_sensor_pin, GPIO.OUT)
GPIO.output(IR_sensor_pin, GPIO.LOW)

# Initialize IR sensor channels for Furnace1, Cooling, and Furance2
F1Channel = 4
CoolChannel = 3
F2Channel = 0

# IMPORTS SET HERE SO PINMODE IS SET PROPERLY FOR EACH IMPORTED MODULE
import STM
from RPI_I2C_ARDUINO import *
from FastRead import * 

# Notebook Class -> Contains Tabs For Process Graphs
class Notebook(fnb.FlatNotebook):
	
	def __init__(self, parent):
		windowstyle = fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NO_X_BUTTON
		fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY, agwStyle=windowstyle)

		self.SetTabAreaColour('white')
		self.heatGraph = heatPanel.TabPanel(self)
		self.coolGraph = coolPanel.TabPanel(self)
		self.reheatGraph = reheatPanel.TabPanel(self)
		self.totalGraph = totalPanel.TabPanel(self)
		
		self.AddPage(self.heatGraph, "Furnace One")
		self.AddPage(self.coolGraph, "Cooling")
		self.AddPage(self.reheatGraph, "Furnace Two") 
		self.AddPage(self.totalGraph, "Total Treatment History") 

# Notebook2 Class -> Contains Left Panel Tabs For Process Control
class Notebook2(fnb.FlatNotebook):
	
	def __init__(self, parent):
		windowstyle = fnb.FNB_NO_NAV_BUTTONS|fnb.FNB_NO_X_BUTTON
		fnb.FlatNotebook.__init__(self, parent, wx.ID_ANY, agwStyle=windowstyle)	
		self.parent = parent
		
		self.simTab = simPanel.TabPanel(self)
		self.AddPage(self.simTab, "Simulation Definition")


# Main User Interface Platform
class MainFrame(wx.Frame):

	def __init__(self, parent, title):
		super(MainFrame, self).__init__(parent, title=title, size=wx.DisplaySize())
		self.mgr = wx.aui.AuiManager(self)
		self.InitUI()
		self.Centre()
		Tk().withdraw()
		
	def InitUI(self):

		# Simulation handling variables
		self.stages = []
		self.startTemps = []
		self.endTemps = []
		self.rates = []
		
		# Gather current date
		self.date = []
		today = datetime.date.today()
		self.date.append(today)
		self.date = str(self.date[0])
		
		# Preload stage for gate
		STM.startStage = 4
		STM.endStage = 4
		 
		# find image path for UI images 		
		imagesPath = os.path.abspath(os.path.join(os.path.dirname(__file__),".."))
		
		# create simulation status bar
		self.status = self.CreateStatusBar()
		
		# Toolbar Menu  
		toolbar = self.CreateToolBar()
		tool1 = toolbar.AddLabelTool(wx.ID_ANY, 'New', wx.Bitmap(os.path.join(imagesPath, 'images/new3.png')))
		tool2 = toolbar.AddLabelTool(wx.ID_ANY, 'Open', wx.Bitmap(os.path.join(imagesPath, 'images/open3.png')))
		tool3 = toolbar.AddLabelTool(wx.ID_ANY, 'Save', wx.Bitmap(os.path.join(imagesPath, 'images/save3.png')))
		tool4 = toolbar.AddLabelTool(wx.ID_ANY, 'Print', wx.Bitmap(os.path.join(imagesPath, 'images/printer3.png')))
		tool5 = toolbar.AddLabelTool(wx.ID_ANY, 'Setting', wx.Bitmap(os.path.join(imagesPath, 'images/setting.png')))
		tool6 = toolbar.AddLabelTool(wx.ID_ANY, 'Quit', wx.Bitmap(os.path.join(imagesPath, 'images/exit3.png')))
		toolbar.SetToolBitmapSize((16,16))
		toolbar.Realize()
		
		# Create Main Panes To Hold Control And Process Settings 
		self.panel1 =panel1= wx.lib.scrolledpanel.ScrolledPanel(parent=self, id=-1, size=(470, 300))
		panel3 = wx.Panel(self, -1, size=(600, 400))
		panel3.SetBackgroundColour('white')
		self.panel4 = panel4 = wx.Panel(self, -1, size=(200, 100))

#--------------------------------------------------------------------------------------------
# Panel 1 corresponds to the left pane of the UI
#--------------------------------------------------------------------------------------------

		panel1.SetupScrolling()
		self.leftpane= leftpane = panel1

		# creating a static box in leftpane
		leftsizer = wx.BoxSizer(wx.VERTICAL)

		# Text Input Used To Define Sample Length For Simulation
		sb1 = wx.StaticBox(leftpane,label='Basic Settings',style=wx.TE_CENTRE)
		sb1.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		
		# Sample Length Input + Default Sample Length
		self.sample = 200
		self.sampleLengthInput = wx.lib.intctrl.IntCtrl(leftpane, 90, self.sample, size=(40, -1),style=wx.TE_RIGHT)
		self.setbutton1 = wx.Button(leftpane, label='SET', size=(40, -1))	
		boxsizer1 = wx.StaticBoxSizer(sb1, wx.HORIZONTAL)
		boxsizer1.Add(wx.StaticText(leftpane, label="Sample Length:"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)		
		boxsizer1.Add(self.sampleLengthInput,flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=3)
		boxsizer1.Add(wx.StaticText(leftpane, label="mm"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		boxsizer1.Add(self.setbutton1, flag=wx.LEFT|wx.ALIGN_RIGHT, border =95)	

		# Stepper Motor Speed Input + Default Stepper Motor Speed
		self.motorSpeed = 120
		sb3 = wx.StaticBox(leftpane, label='Sample Transportation', style=wx.TE_CENTRE)
		sb3.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		self.stepperMotorSpeedInput = wx.lib.intctrl.IntCtrl(leftpane, 91, 120, size=(40, -1),style=wx.TE_RIGHT)
		self.setbutton2 = wx.Button(leftpane, label='SET', size=(40, -1))	
		boxsizer3 = wx.StaticBoxSizer(sb3, wx.HORIZONTAL)
		boxsizer3.Add(wx.StaticText(leftpane, label="Stepper Mottor Speed:"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)		
		boxsizer3.Add(self.stepperMotorSpeedInput,flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=3)
		boxsizer3.Add(wx.StaticText(leftpane, label="rpm"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		boxsizer3.Add(self.setbutton2, flag=wx.LEFT|wx.ALIGN_RIGHT, border =48)

		# creating a separating line between two statcibox
		line1 = wx.StaticLine(leftpane)
		line2 = wx.StaticLine(leftpane)
		line3 = wx.StaticLine(leftpane)
		
		# Live Simulation Readings
		simulationBox = wx.StaticBox(leftpane,label='Real Time Readings',style=wx.TE_CENTRE)
		simulationBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		liveSizer = wx.StaticBoxSizer(simulationBox, wx.VERTICAL)
		
		self.furnLive = wx.Button(leftpane, label="Furnaces Live Monitor", size=(250, 30))
		self.irLive	  = wx.Button(leftpane, label="IR Sensors Live Monitor", size=(250, 30))	
		
		# Notebook2 used to proved a layout for stage, temperature, or cooling point, and hold-time
		self.notebook2 = Notebook2(panel1)
		tempsettingSizer = wx.BoxSizer(wx.VERTICAL)
		tempsettingSizer.Add(self.notebook2, 1, flag = wx.ALL|wx.EXPAND)
		
		liveSizer.Add(self.furnLive, 10, flag=wx.EXPAND, border=4)
		liveSizer.Add(self.irLive, 10, flag=wx.EXPAND, border=4)
		
		leftsizer.Add(boxsizer1, 0, wx.EXPAND)
		leftsizer.Add(line1, 0, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border=5)
		leftsizer.Add(boxsizer3, 0, wx.EXPAND)
		leftsizer.Add(line2, 0, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border=5)
		leftsizer.Add(liveSizer, 0, wx.EXPAND)
		leftsizer.Add(line3, 0, flag=wx.EXPAND|wx.BOTTOM|wx.TOP, border=5)
		leftsizer.Add(tempsettingSizer, 0, wx.EXPAND)

		leftpane.SetSizer(leftsizer)
		
#---------------------------------------------------------------------------------------------
# Panel 3 corresponds to the center panel and involves graphing and plotting process data
#---------------------------------------------------------------------------------------------

		self.notebook = Notebook(panel3)
		panel3sizer = wx.BoxSizer(wx.VERTICAL)

		# Set the sizers
		panel3sizer.Add(self.notebook, 1, flag = wx.ALL|wx.EXPAND)
		panel3.SetSizer(panel3sizer)
		
#---------------------------------------------------------------------------------------------
# Panel 4 corresponds to the right panel and involves running and monitoring the simulation
#---------------------------------------------------------------------------------------------

		# Simulation Information Box
		TestInfoBox = wx.StaticBox(panel4, label='Test Info', style = wx.TE_CENTRE)
		TestInfoBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box3 = wx.StaticBoxSizer(TestInfoBox, wx.VERTICAL)
		self.TestInfo = wx.TextCtrl(panel4, size=(150, -1),style=wx.TE_RIGHT)
		panel4Box3.Add(wx.StaticText(panel4, label="Test Sample Number && Date :"), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		panel4Box3.Add(self.TestInfo, 0, flag = wx.TOP|wx.EXPAND)

		# Furnace Monitor Section
		panel4Sizer = wx.BoxSizer(wx.VERTICAL)
		self.StartBox = wx.StaticBox(panel4, label='Position Control', style=wx.TE_CENTRE)
		self.Furnace_num = 1
		self.StartBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box1 = wx.StaticBoxSizer(self.StartBox, wx.VERTICAL)
		
		# Sample Positioning Buttons
		self.furn1 = wx.Button(panel4, label="Furnace 1", size=(190, 30))
		self.cool = wx.Button(panel4, label="Cooling", size=(190, 30))
		self.furn2 = wx.Button(panel4, label="Furnace 2", size=(190, 30))
		self.load = wx.Button(panel4, label="Loading", size=(190, 30))
		self.stage = wx.Button(panel4, label="STAGE", size=(190, 30))
		
		panel4Box1.Add(self.furn1, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.cool, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.furn2, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.load, 0, wx.EXPAND, 0)
		panel4Box1.Add(self.stage, 0, wx.EXPAND, 0)
	
		# Solenoid Cooling Valve Manual Control
		self.ValveBox = wx.StaticBox(panel4,label='Solenoid Valve Off', style = wx.TE_CENTRE)
		self.ValveBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box4 = wx.StaticBoxSizer(self.ValveBox, wx.VERTICAL)
		self.ValveCon = wx.Button(panel4, label = 'Turn On',size=(190, 30))
		panel4Box4.Add(self.ValveCon, 0, wx.EXPAND, 0)

		# Furnace 1 Preheat Settings
		FurnacePresetBox = wx.StaticBox(panel4, label = 'Preheat Settings', style = wx.TE_CENTRE)
		FurnacePresetBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box5 = wx.StaticBoxSizer(FurnacePresetBox, wx.VERTICAL)
		
		# Furnace 1 Set Point Temperature Setting
		self.furnace1Preset = wx.lib.intctrl.IntCtrl(panel4, 91, 0, size=(45, -1),style=wx.TE_RIGHT)
		self.f1PresetButton = wx.Button(panel4, label = 'SET', size=(40, -1))
		
		FurnacePreset = wx.GridBagSizer(0, 5)
		FurnacePreset.Add(wx.StaticText(panel4, label="FCE 1 Temp:"), pos= (0, 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.furnace1Preset, pos = (0, 1), flag=wx.BOTTOM, border=5)
		FurnacePreset.Add(wx.StaticText(panel4, label="C"), pos = (0, 2), flag=wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.f1PresetButton, pos = (0, 3), flag=wx.RIGHT|wx.BOTTOM, border=5)

		# Furnace 2 Set Point Temperature Setting
		self.furnace2Preset = wx.lib.intctrl.IntCtrl(panel4, 90, 0, size=(45, -1),style=wx.TE_RIGHT)
		self.f2PresetButton = wx.Button(panel4, label = 'SET', size=(40, -1))
		
		FurnacePreset.Add(wx.StaticText(panel4, label="FCE 2 Temp:"), pos = (2, 0), flag=wx.LEFT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.furnace2Preset, pos = (2, 1), flag=wx.BOTTOM, border=5)
		FurnacePreset.Add(wx.StaticText(panel4, label="C"), pos = (2, 2), flag=wx.RIGHT|wx.TOP|wx.BOTTOM, border=5)
		FurnacePreset.Add(self.f2PresetButton, pos = (2, 3), flag=wx.RIGHT|wx.BOTTOM, border=5)

		# Container for all furnace settings
		panel4Box5.Add(FurnacePreset, 0, flag = wx.TOP|wx.EXPAND)
		FurnacePresetBox.SetSizer(panel4Box5)
		panel4Box5.Fit(panel4)

		# Run Simulation Box
		RunBox = wx.StaticBox(panel4,label='Start', style = wx.TE_CENTRE)
		RunBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box2 = wx.StaticBoxSizer(RunBox,wx.VERTICAL)
		self.MainRun = wx.Button(panel4, label = 'Run Simulation',size=(190, 30))
		panel4Box2.Add(self.MainRun, 0, flag = wx.TOP|wx.EXPAND)

		# Show Total Treatment History Box
		self.ShowBox = wx.StaticBox(panel4, label = 'Total Plot', style = wx.TE_CENTRE)
		self.ShowBox.SetFont(wx.Font(12, wx.SWISS, wx.NORMAL, wx.BOLD))
		panel4Box6 = wx.StaticBoxSizer(self.ShowBox, wx.VERTICAL)
		self.ShowPlot = wx.Button(panel4, label = 'Show Total Plot',size=(190, 30))
		panel4Box6.Add(self.ShowPlot, 0, wx.EXPAND, 0)

		# Import Simulation History Box
		self.importSim = wx.Button(panel4, label='Import Simulation Summary', size=(190, 30))
		panel4Box6.Add(self.importSim, 0, wx.EXPAND, 0)
		
		# Set the sizers
		panel4Sizer.Add(panel4Box3, 0, flag = wx.TOP|wx.EXPAND, border=10)
		panel4Sizer.Add(panel4Box1, 0, flag = wx.TOP|wx.EXPAND, border=10)
		panel4Sizer.Add(panel4Box4, 0, flag = wx.TOP|wx.EXPAND, border=10)
		panel4Sizer.Add(panel4Box5, 0,flag = wx.TOP|wx.EXPAND, border=10)
		panel4Sizer.Add(panel4Box2, 0,flag = wx.TOP|wx.EXPAND, border=10)
		panel4Sizer.Add(panel4Box6, 0,flag = wx.TOP|wx.EXPAND, border=10)

		panel4.SetSizer(panel4Sizer)
		
		
#---------------------------------------------------------------------------------------------
# UI Layout: using wx.aui to layout created panels
#---------------------------------------------------------------------------------------------

		#self.mgr.AddPane(panel2, wx.aui.AuiPaneInfo().Bottom().CloseButton(False).CaptionVisible(False))
		self.mgr.AddPane(panel1, wx.aui.AuiPaneInfo().Left().Layer(1).CloseButton(False).CaptionVisible(False))
		self.mgr.AddPane(panel3, wx.aui.AuiPaneInfo().Center().Layer(2).CloseButton(False).CaptionVisible(False))
		self.mgr.AddPane(panel4, wx.aui.AuiPaneInfo().Right().Layer(1).CloseButton(False).CaptionVisible(False))
		self.mgr.Update()
		self.Show()
		
#---------------------------------------------------------------------------------------------
# Event Bindings for UI button presses and text entry events below

		# Bind RedrawTimer for simulation data plotting
		self.redrawTimer = wx.Timer(self)
		self.redrawTimer.Start(10000)
		
		# Simulation Button: 
		self.Bind(wx.EVT_BUTTON, self.onSimulate, self.MainRun)
		
		# Sample Positioning Buttons
		self.Bind(wx.EVT_BUTTON, self.onFurnace1, self.furn1)
		self.Bind(wx.EVT_BUTTON, self.onCool, self.cool)
		self.Bind(wx.EVT_BUTTON, self.onFurnace2, self.furn2)
		self.Bind(wx.EVT_BUTTON, self.onLoad, self.load)
		self.Bind(wx.EVT_BUTTON, self.onStage, self.stage)
		
		# Live Temperature Reading Launchers
		self.Bind(wx.EVT_BUTTON, self.onFurnLive, self.furnLive)
		self.Bind(wx.EVT_BUTTON, self.onIrLive, self.irLive)
						
		# Turn Solenoid On/Off
		self.Bind(wx.EVT_BUTTON, self.onValveCon, self.ValveCon)
		
		# Show All Plots Of Past Simulation
		self.Bind(wx.EVT_BUTTON, self.onShowPlot, self.ShowPlot)

		# Import Old Simulation
		self.Bind(wx.EVT_BUTTON, self.onImportSum, self.importSim)
		
		# Bind timer 
		self.Bind(wx.EVT_TIMER, self.onRedrawTimer, self.redrawTimer)
				
		# Bind Toolbar Events
		self.Bind(wx.EVT_TOOL, self.OnQuit, tool6)
		self.Bind(wx.EVT_TOOL, self.OnSetting, tool5)
				
		self.panel1.Bind(wx.EVT_RIGHT_DOWN, self.OnRightDown)
		self.leftpane.Bind(wx.EVT_BUTTON, self.setSampleLength, self.setbutton1)
		self.sampleLengthInput.Bind(wx.lib.intctrl.EVT_INT, self.setSampleLength)
		self.stepperMotorSpeedInput.Bind(wx.lib.intctrl.EVT_INT, self.setStepperMotorSpeed)
				
		# Bind Update Three Tab Update Buttons To onUpdate Functions 
		self.notebook2.simTab.Bind(wx.EVT_BUTTON, self.onUpdateGraph, self.notebook2.simTab.updateButton)
		
		# Bind Furnace Temp Preset
		self.Bind(wx.EVT_BUTTON, self.presetFurnace1, self.f1PresetButton)
		self.Bind(wx.EVT_BUTTON, self.presetFurnace2, self.f2PresetButton)

	# Reads from file to display plot of process data collected on the graph previously
	def onShowPlot(self,event):
		filename = askopenfilename()
		filename = filename.split('/')[-1]
		filename = filename.split('-')[0]+'-'+filename.split('-')[1]+'-'+filename.split('-')[2]+'-'+filename.split('-')[3]
		print filename
		
		self.notebook.heatGraph.plotFromFile(filename)
		self.notebook.coolGraph.plotFromFile(filename)
		self.notebook.reheatGraph.plotFromFile(filename)
		self.notebook.totalGraph.plotFromFile(filename)
		
	def onImportSum(self, event):
		
		filename = askopenfilename()
		filename = filename.split('/')[-1]
		# Sorry for strange parsing: (ex. file-[2017-9-04])
		filename = filename.split('-')[0]+'-'+filename.split('-')[1]+'-'+filename.split('-')[2]+'-'+filename.split('-')[3]
		print filename
		
		stages, startTemps, endTemps, setRates = sim.importSummary(filename)
		
		self.notebook2.simTab.removeAllWidgets()
		self.notebook2.simTab.addMultipleWidgets(stages, startTemps, endTemps, setRates)
		
	# Changes the UI to display furnace 1 or furnace 2 information
	def onSwitchFCE(self, event):
		if self.Furnace_num == 1:
			self.StartBox.SetLabel('Furnace 2 Status')
			self.Furnace_num = 2
		else:
			self.StartBox.SetLabel('Furnace 1 Status')
			self.Furnace_num = 1

	# Set the CURRENT PRESET of Furnace 1
	def presetFurnace1(self, event):
		if self.furnace1Preset.GetValue() != 0:
			setTemp(01, int(self.furnace1Preset.GetValue()), fc.ser)
		else:
			print "Furnace 1 temp has not been set yet."
			
	# Set the CURRENT PRESET of Furnace 2		
	def presetFurnace2(self, event):
		if self.furnace2Preset.GetValue() != 0:
			setTemp(02, self.furnace2Preset.GetValue(), fc.ser)
		else:
			print "Furnace 2 temp has not been set yet."
		
	# Read Up Ramp Of The Furance
	def onGetUPR(self,event):
		hex_temp = getUPR("01", fc.ser)[7:11]
		temp = int(hex_temp,16)
		print "current Up Ramp:" 
		print temp, "C/min"

	# Read Down Ramp Of The Furnace
	def onGetDNR(self, event):
		hex_temp = getDNR("01", fc.ser)[7:11]
		temp = int(hex_temp,16)
		print "current Down Ramp:" 
		print temp, "C/min"

	# Read Current Set Point Of The Furnace
	def onGetCSP(self, event):
		if self.Furnace_num == 1:
			hex_temp = getCSP("01", fc.ser)[7:11]
			temp = int(hex_temp,16)
			print "current FCE 1 setpoint temp:" 
			print temp
		else:
			hex_temp = getCSP("02", fc.ser)[7:11]
			temp = int(hex_temp,16)
			print "current FCE 2 setpoint temp:" 
			print temp
			
		return temp	


	# Read Temperature Of The Furnace
	def onGetTemp(self, event):
		if self.Furnace_num == 1:
			# this function is reading the temperature from the furnace built-in controller
			hex_temp = getPV("01", ser)[7:11]
			print "HEX"
			print hex_temp
			temp = int(hex_temp, 16)	
		
			print "current FCE 1 temp:" 
			print temp
		else:
			hex_temp = getPV("02", ser)[7:11]
			temp = int(hex_temp, 16)
			
			print "current FCE 2 temp:" 
			print temp
		
		return temp

	# Toggle Status of the cooling valves solenoid
	def onValveCon(self, event):
		if GPIO.input(coolingValvePin) == 0:
			GPIO.output(coolingValvePin, GPIO.HIGH)
			self.ValveCon.SetLabel('Turn Off')
			self.ValveBox.SetLabel('Solenoid Valve On')
			print "off"
		else:
			GPIO.output(coolingValvePin, GPIO.LOW)
			self.ValveCon.SetLabel('Turn On')
			self.ValveBox.SetLabel('Solenoid Valve Off')
			print "on"
				
	# Run The Entire Simulation As Specified In The Simulation Panel	
	#def simulate(self, *args, **kwargs):
	def onSimulate(self, event):
		
		self.gridIndex = 0
		lastTime = 0
						
		self.stages = self.notebook2.heatGraph.stages
		self.tempsStart = self.notebook2.heatGraph.startTemps
		self.tempsEnd = self.notebook2.heatGraph.endTemps
		self.setRates = self.notebook2.heatGraph.setRates

		self.notebook.heatGraph.reset()
		self.notebook.coolGraph.reset()
		self.notebook.reheatGraph.reset()
		self.notebook.totalGraph.reset()

		self.stages = [x for x in self.stages if x is not None]
		self.tempsStart = [x for x in self.tempsStart if x is not None]
		self.tempsEnd = [x for x in self.tempsEnd if x is not None]
		self.setRates = [x for x in self.setRates if x is not None]
			
		self.hasCooling = [x for x in self.stages if x is 2]
		self.hasEnd = [x for x in self.stages if x is 4]
		
		# Make sure GPIO state is good
		GPIO.output(IR_sensor_pin, GPIO.LOW)
		GPIO.output(coolingValvePin, GPIO.LOW)
		
		# Considers end cases and safety concerns based on cycles (purely my own opinion, I could be wrong in assuming)
		if len(self.stages) == 0:
			print "Please select stages before running simulation (ex. Furnace1, Cool, Furnace2, Cool, Load)"
			self.status.SetStatusText("")
			return
		
		if len(self.hasCooling) == 0 and (max(self.tempsStart) >= 300 or max(self.tempsEnd) >= 300):
			print "Simulation requires a cooling stage, if there is no cooling this treatment is unsafe, this is a fail-safe to prevent damage or harm. If you need to preform this operation and are limited by this case visit line 1226 in the code and change the max(~) temperature values"
			self.status.SetStatusText("")
			return
			
		if len(self.hasEnd) == 0:
			print "Simulation has no end load stage, to move sample back to the loading position please use settings panel in the menu toolbar to move sample manually"
			self.status.SetStatusText("")
			return				
				
		print "Stages    : %r" %self.stages	
		print "StartTemps: %r" %self.tempsStart
		print "EndTemps  : %r" %self.tempsEnd
		print "Rates     : %r" %self.setRates	
			
		index = 0
		rampDir = 0	 # 1-> UP Ramp -1-> DOWN Ramp 0-> NO Ramp (Hold)
		
		print "Stages: %r" %len(self.stages)
		self.status.SetStatusText("Stages: %r" %len(self.stages))		
		startTime = time.time()
		
		for stage in self.stages:
			
			if stage == STM.Furnace_1:
				print "Furance 1 - Heating Stage"
				self.status.SetStatusText("Furance 1 - Heating Stage")
				
				# gather control information
				startTemp = self.tempsStart[index]
				endTemp = self.tempsEnd[index]
				hold = 0
				
				if startTemp == endTemp:
					hold = self.setRates[index]
					rampDir = 0
				elif startTemp < endTemp:
					ramp = self.setRates[index]
					rampDir = 1
				elif startTemp > endTemp:
					ramp = self.setRates[index]
					rampDir = -1
					
				# Set Furnace 1 Temps and Ramps	
				if startTemp <= 250:		
					util.setFurnace1Temp(endTemp)
					print "Furnace 1 temperature set to: %r" %endTemp
					self.status.SetStatusText("Furnace 1 temperature set to: %r" %endTemp)
					furnaceTemp = util.getFurnace1Temp()
					upperTemp = endTemp + pad
					lowerTemp = endTemp - pad
				else:
					util.setFurnace1Temp(startTemp)
					print "Furnace 1 temperature set to: %r" %startTemp
					self.status.SetStatusText("Furnace 1 temperature set to: %r" %startTemp)
					furnaceTemp = util.getFurnace1Temp()
					upperTemp = startTemp + pad
					lowerTemp = startTemp - pad
				
				print "bringing furnace up to start temperature..."
				self.status.SetStatusText("bringing furnace up to start temperature...")
				
				if rampDir == 1 or rampDir == 0:
					# Wait for furnace temperature to reach the desired start temperature
					while furnaceTemp < lowerTemp:
						furnaceTemp = util.getFurnace1Temp()
						time.sleep(0.1)
						print "waiting until furnace 1 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp)
						self.status.SetStatusText("waiting until furnace 1 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp))	
				elif rampDir == -1:
					# Wait for furnace temperature to reach the desired start temperature
					while furnaceTemp < lowerTemp or furnaceTemp > upperTemp:
						furnaceTemp = util.getFurnace1Temp()
						time.sleep(0.1)
						print "waiting until furnace 1 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp)
						self.status.SetStatusText("waiting until furnace 1 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp))		
							
				print "Beginning heat treatment"	
				self.status.SetStatusText("Beginning heat treatment")
				# Start Furnace Cycle ------------------------------------------------			
				print "Moving sample to furance 1 position"
				self.status.SetStatusText("Moving sample to furance 1 position")	

				# move and delay to make certain sample is positioned correctly before reading
				moveToFurnace1(self)
				time.sleep(7)

				fTimes, fReads, lastTime = fastReadFurnace(30, startTemp, endTemp, F1Channel, hold, self.notebook.heatGraph, self.notebook.totalGraph, lastTime)
				print "Process finished, data captured"
				self.status.SetStatusText("Process finished, data captured")
				
				print "stage {} finished in {} seconds".format(stage, int(time.time() - startTime))
				self.status.SetStatusText("stage {} finished in {} seconds".format(stage, int(time.time() - startTime)))
				# End Furnace Cycle --------------------------------------------------
				
				index += 1	
					
			elif stage == STM.Cool:
				print "Cooling Area - Cooling Stage"
				self.status.SetStatusText("Cooling Area - Cooling Stage")
				
				# gather control information
				startTemp = self.tempsStart[index]
				endTemp = self.tempsEnd[index]
				sampleRate = self.setRates[index]
				
				if sampleRate < 0 or sampleRate > 30: 
					print "invalid sampling rate %r using default" %samplingRate
					self.status.SetStatusText("invalid sampling rate %r using default" %samplingRate)
					sampleRate = 30	
					
				print "Beginning Cooling Process"
				self.status.SetStatusText("Beginning Cooling Process")	
				# Start Cool Cycle -----------------------------------------------------	
				print "Moving sample to cooling area"
				self.status.SetStatusText("Moving sample to cooling area")
				
				# move and delay to make certain sample is positioned correctly before reading
				moveToCoolingArea(self)
				time.sleep(4)
				
				GPIO.output(coolingValvePin, GPIO.HIGH)
				cTimes, cReads, lastTime = fastReadCooling(30, startTemp, endTemp, CoolChannel, self.notebook.coolGraph, self.notebook.totalGraph, lastTime)
				GPIO.output(coolingValvePin, GPIO.LOW)	
				print "Process finished, data captured"
				self.status.SetStatusText("Process finished, data captured")
				
				print "stage {} finished in {} seconds".format(stage, int(time.time() - startTime))
				self.status.SetStatusText("stage {} finished in {} seconds".format(stage, int(time.time() - startTime)))
				# End Cool Cycle -------------------------------------------------------	
					
				index += 1
			
			elif stage == STM.Furnace_2:
				print "Furnace 2 - Reheating Stage"
				self.status.SetStatusText("Furnace 2 - Reheating Stage")
								
				# gather control information				
				startTemp = self.tempsStart[index]
				endTemp = self.tempsEnd[index]
				ramp = self.setRates[index]
				hold = 0
				
				if startTemp == endTemp:
					hold = self.setRates[index]
					ramp = 0
				elif startTemp < endTemp:
					ramp = self.setRates[index]
					rampDir = 1
				elif startTemp > endTemp:
					ramp = self.setRates[index]
					rampDir = -1
					
				# Set Furnace 2 Temps and Ramps	
				if startTemp <= 250:		
					util.setFurnace2Temp(endTemp)
					print "Furnace 2 temperature set to: %r" %endTemp
					self.status.SetStatusText("Furnace 2 temperature set to: %r" %endTemp)
					furnaceTemp = util.getFurnace2Temp()
					upperTemp = endTemp + pad
					lowerTemp = endTemp - pad
				else:
					util.setFurnace2Temp(startTemp)
					print "Furnace 2 temperature set to: %r" %endTemp
					self.status.SetStatusText("Furnace 2 temperature set to: %r" %endTemp)
					furnaceTemp = util.getFurnace2Temp()
					upperTemp = startTemp + pad
					lowerTemp = startTemp - pad
				
				self.status.SetStatusText("bringing furnace up to starting temp...")
				# Wait for furnace 2 temperature to reach the desired start temperature
				if rampDir == 1 or rampDir == 0:
					while furnaceTemp < lowerTemp:
						furnaceTemp = util.getFurnace2Temp()
						time.sleep(0.1)
						print "waiting until furnace 2 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp)
						self.status.SetStatusText("waiting until furnace 1 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp))	
				elif rampDir == -1:
					# Wait for furnace temperature to reach the desired start temperature
					while furnaceTemp < lowerTemp or furnaceTemp > upperTemp:
						furnaceTemp = util.getFurnace2Temp()
						time.sleep(0.1)
						print "waiting until furnace 2 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp)
						self.status.SetStatusText("waiting until furnace 1 temp {} is between {} and {}".format(furnaceTemp, lowerTemp, upperTemp))		
				
				print "Beginning reheat treatment"
				self.status.SetStatusText("Beginning reheat treatment")	
				# Start Furnace Cycle ------------------------------------------------			
				print "Moving sample to furance 2 position"
				self.status.SetStatusText("Moving sample to furance 2 position")
				
				# move and delay to make certain sample is positioned correctly before reading
				moveToFurnace2(self)
				time.sleep(4)
				
				f2Times, f2Reads, lastTime = fastReadFurnace(30, startTemp, endTemp, F2Channel, hold, self.notebook.reheatGraph, self.notebook.totalGraph, lastTime)
				print "Process finished, data collected"
				self.status.SetStatusText("Process finished, data collected")
								
				print "stage {} finished in {} seconds".format(stage, int(time.time() - startTime))
				self.status.SetStatusText("stage {} finished in {} seconds".format(stage, int(time.time() - startTime)))
				# End Furnace 2 Cycle ---------------------------------------------------
				
				index += 1
			
			elif stage == STM.Load:
				print "Load - Simulation End Stage"
				self.status.SetStatusText("Load - Simulation End Stage")
				
				# Make sure GPIO state is good
				GPIO.output(IR_sensor_pin, GPIO.LOW)
				GPIO.output(coolingValvePin, GPIO.LOW)	
				
				moveToLoad(self)
				
				print "stage {} finished in {} seconds".format(stage, int(time.time() - startTime))
				self.status.SetStatusText("stage {} finished in {} seconds".format(stage, int(time.time() - startTime)))
				print "End of simulation, please use caution sample could still be hot!!!"
				self.status.SetStatusText("End of simulation, please use caution sample could still be hot!!!")
				
				index += 1
				return	
		
			
			

	def onUpdateGraph(self, event):
		
		self.status.SetStatusText("Graph has been updated with estimate values")
		pfile = self.TestInfo.GetValue()
		
		# Graphs The Estimated Simulation Expectancy
		self.stages = self.notebook2.simTab.stages
		self.tempsStart = self.notebook2.simTab.startTemps
		self.tempsEnd = self.notebook2.simTab.endTemps
		self.setRates = self.notebook2.simTab.setRates
		
		pfile = self.TestInfo.GetValue()
		if pfile == '':
			pfile = "lastSimulation"
			sim.writeSummary(pfile, self.stages, self.tempsStart, self.tempsEnd, self.setRates)
		else:
			sim.writeSummary(pfile, self.stages, self.tempsStart, self.tempsEnd, self.setRates)
		
		# initialize estimate collection lists
		self.furnace1Temps = []
		self.furnace1Times = []
		self.coolingTemps = []
		self.coolingTimes = []
		self.furnace2Temps = []
		self.furnace2Times = []
		self.totalTimes = []
		self.totalTemps = []
		index = 0
		
		# Reset data if a new simulation would like to be ran
		self.notebook.heatGraph.reset()
		self.notebook.coolGraph.reset()
		self.notebook.reheatGraph.reset()
		self.notebook.totalGraph.reset()
		
		# Reset estimates initially to remove past simulation data plots
		self.notebook.heatGraph.resetEst()
		self.notebook.coolGraph.resetEst()
		self.notebook.reheatGraph.resetEst()
		self.notebook.totalGraph.resetEst()
		
		# parse stage list
		for stage in self.stages: 
			if stage == util.Furnace_1:
				self.furnace1Temps.append(self.tempsStart[index])
				self.furnace1Temps.append(self.tempsEnd[index])
				self.totalTemps.append(self.tempsStart[index])
				self.totalTemps.append(self.tempsEnd[index])
						
				if self.tempsStart[index] == self.tempsEnd[index]:
					self.furnace1Times.append(self.setRates[index])
					self.totalTimes.append(self.setRates[index]);
				else:
					diff = abs(self.tempsStart[index] - self.tempsEnd[index])
					if self.setRates[index] != 0:
						ramp = diff/self.setRates[index]
					else:
						print "must set furnace 1 time ramp/hold: default = 10"
						ramp = 10	
					
					self.furnace1Times.append(ramp)
					self.totalTimes.append(ramp);
					
				index += 1
			elif stage == util.Cool:
				self.coolingTemps.append(self.tempsStart[index])
				self.coolingTemps.append(self.tempsEnd[index])
				self.totalTemps.append(self.tempsStart[index])
				self.totalTemps.append(self.tempsEnd[index])
					
				self.coolingTimes.append(abs(self.tempsStart[index] - self.tempsEnd[index])/self.setRates[index])	
				self.totalTimes.append(abs(self.tempsStart[index] - self.tempsEnd[index])/self.setRates[index])
				
				index += 1
			elif stage == util.Furnace_2:
				self.furnace2Temps.append(self.tempsStart[index])
				self.furnace2Temps.append(self.tempsEnd[index])
				self.totalTemps.append(self.tempsStart[index])
				self.totalTemps.append(self.tempsEnd[index])
				
				if self.tempsStart[index] == self.tempsEnd[index]:
					self.furnace2Times.append(self.setRates[index])
					self.totalTimes.append(self.setRates[index])
				else:
					diff = abs(self.tempsStart[index] - self.tempsEnd[index])
					if self.setRates[index] != 0:
						ramp = diff/self.setRates[index]
					else:
						print "must set a furnace 2 time ramp/hold: default = 10"
						ramp = 10
						
					self.furnace2Times.append(ramp)
					self.totalTimes.append(ramp)
				
				index += 1
			elif stage == util.Load:
				# no loading temps graphed
				index += 1
		
		print "Furnace 1 Temps %r" %self.furnace1Temps
		print "Furance 1 Times %r" %self.furnace1Times
		print "Cooling Temps   %r" %self.coolingTemps
		print "Cooling Times   %r" %self.coolingTimes
		print "Furnace 2 Temps %r" %self.furnace2Temps
		print "Furnace 2 Times %r" %self.furnace2Times
		print "Total Temps     %r" %self.totalTemps[2:]
		print "Total Times     %r" %self.totalTimes
		
		self.furnace1Times = util.parseTimeSequence(self.furnace1Times)
		self.coolingTimes = util.parseTimeSequence(self.coolingTimes)
		self.furnace2Times = util.parseTimeSequence(self.furnace2Times)
		self.totalTimes = util.parseTimeSequence(self.totalTimes)		
				
		self.furnace1Temps = [x for x in self.furnace1Temps if x is not None]
		self.furnace1Times = [x for x in self.furnace1Times if x is not None]
		self.coolingTemps =  [x for x in self.coolingTemps if x is not None]
		self.coolingTimes =  [x for x in self.coolingTimes if x is not None]
		self.furnace2Temps = [x for x in self.furnace2Temps if x is not None]
		self.furnace2Times = [x for x in self.furnace2Times if x is not None]
		self.totalTemps =    [x for x in self.totalTemps if x is not None]
		self.totalTimes =    [x for x in self.totalTimes if x is not None]

		# Set Values For (x, y) => (time, temp) For Simulation Estimate Plots
		
		# Furnace 1 Estimates
		self.notebook.heatGraph.drawEstPlot(self.furnace1Times, self.furnace1Temps)
		
		# Cooling Estimates
		self.notebook.coolGraph.drawEstPlot(self.coolingTimes, self.coolingTemps)
		
		# Furnace 2 Estimates
		self.notebook.reheatGraph.drawEstPlot(self.furnace2Times, self.furnace2Temps)
		
		# Total Estimates
		self.notebook.totalGraph.drawEstPlot(self.totalTimes, self.totalTemps)
		
		
	# For periodically redrawing graphs live
	def onRedrawTimer(self, event):
		
		pfile = self.TestInfo.GetValue()
		
		if len(pfile) > 0:
			self.notebook.heatGraph.recordData(pfile)
			self.notebook.coolGraph.recordData(pfile)
			self.notebook.reheatGraph.recordData(pfile)
			self.notebook.totalGraph.recordData(pfile)
		else:
			pfile = "lastSimulation"
			self.TestInfo.SetValue(pfile)
			self.notebook.heatGraph.recordData(pfile)
			self.notebook.coolGraph.recordData(pfile)
			self.notebook.reheatGraph.recordData(pfile)
			self.notebook.totalGraph.recordData(pfile)
		
		
	# Set Panel 1 Focus
	def onFocus(self, event):
		self.panel1.SetFocus()	
	
	# Set the sample length for the simulation
	def setSampleLength(self, event):
		self.sample = self.sampleLengthInput.GetValue()
		
		print "Update Sample Length: %r" %self.sample
		
	# Set the stepper motor speed for the simulation	
	def setStepperMotorSpeed(self, event):
		self.motorSpeed = self.stepperMotorSpeedInput.GetValue()
		
		print "Update Motor Speed: %r" %self.motorSpeed	

	# Quit Application
	def OnQuit(self, e):
		GPIO.cleanup();
		self.Close()

	# Open CAL Testing Harness
	def OnSetting(self, e):
		self.Setting = STM.STM_T()
		self.Setting.Show()
		
	def onFurnLive(self, event):
		print "Launched Furnace Live Monitor"
		self.fLive = furn.LiveFurnaceFrame()
		self.fLive.Show()
		
	def onIrLive(self, event):
		print "Launched IR Live Monitor"
		self.iLive = ir.LiveIRFrame()
		self.iLive.Show()		

	# Popup Menu 
	def OnRightDown(self, e):
		self.PopupMenu(MyPopupMenu(self.panel1), e.GetPosition())
	
	# Button tie in's	
	def onFurnace1(self, event):
		util.moveToFurnace1(self)
		
	def onCool(self, event):
		util.moveToCoolingArea(self)
		
	def onFurnace2(self, event):
		util.moveToFurnace2(self)
	
	def onLoad(self, event):
		util.moveToLoad(self)
		
	def onStage(self, event):
		util.stageSample(self)					
		
# Simple popup menu example
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

# Run simulator and start solenoid thread to control gate operation during simulation
def main():
	gateThread = threading.Thread(target = gt.gateThread)
	gateThread.start()
	ex = wx.App(redirect=False)
	MainFrame(None, "CAL Simulator")
	ex.MainLoop()
			
if __name__=='__main__':
	main()


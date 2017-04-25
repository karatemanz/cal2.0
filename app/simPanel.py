import wx
import wx.lib.intctrl
import wx.lib.masked as masked

def getSec(time):
	l = str(time)[1:]
	l = l.split(':')
	return int(l[0]) * 3600 + int(l[1]) * 60 + int(l[2])

class TabPanel(wx.Panel):
	def __init__(self, parent):

		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
		self.numButtons = 0
		self.stages = [None]*15
		self.startTemps = [None]*15
		self.endTemps = [None]*15
		self.setRates = [None]*15

		self.frame = parent
		self.mainSizer = wx.BoxSizer(wx.VERTICAL)
		controlSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.widgetSizer = wx.BoxSizer(wx.VERTICAL)
		instructionSizer = wx.BoxSizer(wx.HORIZONTAL)

		self.addButton = wx.Button(self, label="Add", size=(-1, -1))
		self.addButton.Bind(wx.EVT_BUTTON, self.onAddWidget)
		controlSizer.Add(self.addButton, 0, wx.CENTER|wx.TOP|wx.RIGHT, 5)

		self.removeButton = wx.Button(self, label="Remove", size=(-1, -1))
		self.removeButton.Bind(wx.EVT_BUTTON, self.onRemoveWidget)
		controlSizer.Add(self.removeButton, 0, wx.CENTER|wx.TOP|wx.RIGHT|wx.LEFT, 5)

		self.updateButton = wx.Button(self, label="Update", size=(-1, -1))
		controlSizer.Add(self.updateButton, 0, wx.CENTER|wx.TOP|wx.LEFT, 5)

		self.newSetpoint = wx.StaticText(self, label='Presets:', size=(70, 20))
		instructionSizer.Add(self.newSetpoint, 0, wx.LEFT, 10)

		self.newStage = wx.StaticText(self, label='Stage:', size=(70, 20))
		instructionSizer.Add(self.newStage, 0, wx.LEFT, 10)

		self.newSetStartTemp = wx.StaticText(self, label='Start Temp:', size=(70, 20))
		instructionSizer.Add(self.newSetStartTemp, 0, wx.LEFT, 10)

		self.newSetEndTemp = wx.StaticText(self, label='End Temp:', size=(70, 20))
		instructionSizer.Add(self.newSetEndTemp, 0, wx.LEFT, 10)

		self.newSetRate = wx.StaticText(self, label='Rate(C/s):', size=(70, 20))
		instructionSizer.Add(self.newSetRate, 0, wx.LEFT, 10)

		self.Bind(wx.EVT_TEXT, self.UpdateText)

		self.mainSizer.Add(controlSizer, 0, wx.CENTER)
		self.mainSizer.Add(instructionSizer, 0, wx.CENTER)
		self.mainSizer.Add(self.widgetSizer, 0, wx.CENTER)
		self.SetSizer(self.mainSizer)

	def UpdateText(self, event):
		#make sure the right text boxes are selected
		
		self.object = event.GetEventObject()
		eventId = self.object.GetId()
		#print "ID: %r" %eventId
		
		if(event.GetId() <= self.numButtons and eventId>=1 and eventId<=100):
			print "Stage: %r" %self.object.GetValue()
			
			stageTxt = self.object.GetValue()
			
			if(stageTxt == "Furnace1"):
				self.stages[eventId-1] = 1
			elif(stageTxt == "Cooling"):
				self.stages[eventId-1] = 2
			elif(stageTxt == "Furnace2"):
				self.stages[eventId-1] = 3
			elif(stageTxt == "Load"):
				self.stages[eventId-1] = 4
				
		if(event.GetId() <= self.numButtons+100 and eventId>=101 and eventId<=200):
			#print "startTemp %r" %self.object.GetValue()
			self.startTemps[eventId-101] = self.object.GetValue()
			
		if(event.GetId() <= self.numButtons+200 and eventId>=201 and eventId<=300):
			#print "endTemp %r" %self.object.GetValue()
			self.endTemps[eventId-201] = self.object.GetValue()
			
		if(event.GetId() <= self.numButtons+300 and eventId>=301 and eventId<=400):			
			#print "rate %r" %self.object.GetValue()
			self.setRates[eventId-301] = self.object.GetValue()

	def onAddWidget(self, event):
		
		# Create New Set Point Identity
		self.numButtons += 1
		label = "Set Point %s :" %self.numButtons
		name = "SP%s" %self.numButtons
		ID = self.numButtons
		self.newSP = wx.StaticText(self, ID, label=label, name=name)
		
		# Add Stage Selection Combo Box
		self.newStage = wx.ComboBox(self, ID, style=wx.CB_DROPDOWN, choices=['Furnace1','Cooling', 'Furnace2', 'Load'])
		
		# Add Start Temp Text Box
		self.newStartTemp = wx.lib.intctrl.IntCtrl(self, ID+100, size=(40, -1), style=wx.TE_RIGHT, name=name)
		self.tempStartUnit = wx.StaticText(self, ID, label = "C", name=name)
		
		# Add End Temp Text Box
		self.newEndTemp = wx.lib.intctrl.IntCtrl(self, ID+200, size=(40, -1), style=wx.TE_RIGHT, name=name)
		self.tempEndUnit = wx.StaticText(self, ID, label = "C", name=name)
		
		# Add Temp Rate Text Box
		self.newRate = wx.lib.intctrl.IntCtrl(self, ID+300, size=(40, -1),style=wx.TE_RIGHT, name=name)
		self.rateUnit = wx.StaticText(self,ID , label = "sec", name=name)
		
		# Add All Components To The 
		self.SPsizer = wx.BoxSizer(wx.HORIZONTAL)
		self.SPsizer.Add(self.newSP, 0,  wx.CENTER|wx.RIGHT, 5)
		self.SPsizer.Add(self.newStage, 0, wx.ALL|wx.EXPAND, 5)
		self.SPsizer.Add(self.newStartTemp, 0,  wx.ALL|wx.EXPAND, 5)
		self.SPsizer.Add(self.tempStartUnit, 0,  wx.ALL|wx.EXPAND, 5)
		self.SPsizer.Add(self.newEndTemp, 0, wx.ALL|wx.EXPAND, 5)
		self.SPsizer.Add(self.tempEndUnit, 0, wx.ALL|wx.EXPAND, 5)
		self.SPsizer.Add(self.newRate, 0, wx.ALL|wx.EXPAND, 5)
		self.SPsizer.Add(self.rateUnit, 0, wx.ALL|wx.EXPAND, 5)
		self.widgetSizer.Add(self.SPsizer, 0, wx.TOP, 5)
		self.frame.Fit()

	def onRemoveWidget(self, event):
		if self.widgetSizer.GetChildren():
			self.widgetSizer.Hide(self.numButtons-1)
			self.widgetSizer.Remove(self.numButtons-1)
			self.numButtons -= 1
			self.stages[self.numButtons] = None
			self.startTemps[self.numButtons] = None
			self.endTemps[self.numButtons] = None
			self.setRates[self.numButtons] = None
			self.frame.Fit()
			
	def removeAllWidgets(self):
		while self.widgetSizer.GetChildren():
			self.widgetSizer.Hide(self.numButtons-1)
			self.widgetSizer.Remove(self.numButtons-1)
			self.numButtons -= 1
			self.stages[self.numButtons] = None
			self.startTemps[self.numButtons] = None
			self.endTemps[self.numButtons] = None
			self.setRates[self.numButtons] = None
			self.frame.Fit()
			
	def addMultipleWidgets(self, newStages, newStartTemps, newEndTemps, newRates):
		
		index = 0
		
		for nStage in newStages:
			# Create New Set Point Identity
			self.numButtons += 1
			label = "Set Point %s :" %self.numButtons
			name = "SP%s" %self.numButtons
			ID = self.numButtons
			self.newSP = wx.StaticText(self, ID, label=label, name=name)
			
			# Add Stage Selection Combo Box
			self.newStage = wx.ComboBox(self, ID, style=wx.CB_DROPDOWN, choices=['Furnace1','Cooling', 'Furnace2', 'Load'])
			
			self.newStage.SetSelection(newStages[index]-1)
			
			if newStages[index] == 1:
				self.newStage.SetValue("Furnace1")
			elif newStages[index] == 2:
				self.newStage.SetValue("Cooling")
			elif newStages[index] == 3:
				self.newStage.SetValue("Furnace2")
			else:
				self.newStage.SetValue("Load")

			event = wx.CommandEvent(wx.wxEVT_COMMAND_COMBOBOX_SELECTED,ID)
			event.SetEventObject(self.newStage)	
			self.UpdateText(event)
			
			print self.newStage.GetValue()		
						
			# Add Start Temp Text Box
			self.newStartTemp = wx.lib.intctrl.IntCtrl(self, ID+100, size=(40, -1), style=wx.TE_RIGHT, name=name)
			self.tempStartUnit = wx.StaticText(self, ID, label = "C", name=name)
			
			self.newStartTemp.SetValue(int(newStartTemps[index]))
			
			# Add End Temp Text Box
			self.newEndTemp = wx.lib.intctrl.IntCtrl(self, ID+200, size=(40, -1), style=wx.TE_RIGHT, name=name)
			self.tempEndUnit = wx.StaticText(self, ID, label = "C", name=name)
			
			self.newEndTemp.SetValue(int(newEndTemps[index]))
			
			# Add Temp Rate Text Box
			self.newRate = wx.lib.intctrl.IntCtrl(self, ID+300, size=(40, -1),style=wx.TE_RIGHT, name=name)
			self.rateUnit = wx.StaticText(self,ID , label = "sec", name=name)
			
			self.newRate.SetValue(int(newRates[index]))
			
			# Add All Components To The 
			self.SPsizer = wx.BoxSizer(wx.HORIZONTAL)
			self.SPsizer.Add(self.newSP, 0,  wx.CENTER|wx.RIGHT, 5)
			self.SPsizer.Add(self.newStage, 0, wx.ALL|wx.EXPAND, 5)
			self.SPsizer.Add(self.newStartTemp, 0,  wx.ALL|wx.EXPAND, 5)
			self.SPsizer.Add(self.tempStartUnit, 0,  wx.ALL|wx.EXPAND, 5)
			self.SPsizer.Add(self.newEndTemp, 0, wx.ALL|wx.EXPAND, 5)
			self.SPsizer.Add(self.tempEndUnit, 0, wx.ALL|wx.EXPAND, 5)
			self.SPsizer.Add(self.newRate, 0, wx.ALL|wx.EXPAND, 5)
			self.SPsizer.Add(self.rateUnit, 0, wx.ALL|wx.EXPAND, 5)
			self.widgetSizer.Add(self.SPsizer, 0, wx.TOP, 5)
			self.frame.Fit()
			
			index += 1
			
class MyFrame(wx.Frame):
    """"""
 
    #----------------------------------------------------------------------
    def __init__(self):
        """Constructor"""
        wx.Frame.__init__(self, parent=None, title="Add / Remove Buttons")
        self.fSizer = wx.BoxSizer(wx.VERTICAL)
        panel = TabPanel(self)
        self.fSizer.Add(panel, 1, wx.EXPAND)
        self.SetSizer(self.fSizer)
        self.Fit()
        self.Show()
        
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App()
    frame = MyFrame()
    app.MainLoop()

import wx
import wx.aui as aui
import wx.lib.intctrl as ic
import wx.lib.scrolledpanel as sp


# Initial harness to run the simulation in a seperate frame to avoid locking up the main GUI during simulations
class Simulator(wx.Frame, stages, startTemps, endTemps, setRates):

	def __init__(self):
		
		wx.Frame.__init__(self,None, title= 'Simulator Summmary Panel', size=(600, 500))
		self.Centre()
		self.textPanel = sp.ScrolledPanel(self)
		self.menuPanel = wx.Panel(self)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		menuSizer = wx.BoxSizer(wx.HORIZONTAL)
		self.textSizer = wx.BoxSizer(wx.VERTICAL)
		
		self.stages = stages
		self.startTemps = startTemps
		self.endTemps = endTemps
		self.setRates = setRates
		
		summaryText = wx.StaticText(textPanel, -1, "Summary:")
		
		summaryButton = wx.Button(menuPanel, label='SUMMARY')
		self.menuPanel.Bind(wx.EVT_BUTTON, self.onSummary, summaryButton)
		
		goButton = wx.Button(menuPanel, label='GO')
		self.menuPanel.Bind(wx.EVT_BUTTON, self.onGo, goButton)
		
		menuSizer.Add(summaryButton)
		menuSizer.Add(goButton)

		sizer.Add(self.textPanel)
		sizer.Add(self.textSizer)
		sizer.Add(self.menuPanel)
		sizer.Add(menuSizer)
		
		self.SetSizer(sizer)
		
	def addSimOut(text):
		textOut = wx.StaticText(textPanel, -1, text)
		self.textSizer.Add(textOut)
		self.frame.Fit()	
		
	def onSummary(self, event):
		
		
	def onGo(self, event):
		print "go"

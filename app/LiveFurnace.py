import util as util
import wx
import wx.aui as aui
import wx.lib.intctrl as ic
import wx.lib.scrolledpanel as sp


# Initial harness to run the simulation in a seperate frame to avoid locking up the main GUI during simulations
class LiveFurnaceFrame(wx.Frame):

	def __init__(self):
		
		wx.Frame.__init__(self,None, title= 'Live Furnace Readings Panel', size=(600, 500))
		self.Centre()
		self.livePanel = wx.Panel(self)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.redrawTemps = wx.Timer(self)
		self.redrawTemps.Start(1000)
			
		self.redrawSettings = wx.Timer(self)
		self.redrawSettings.Start(60000)	
			
		self.titleLabel = wx.StaticText(self.livePanel, label='Furnace 1 and 2 Live Status Monitor')
		
		self.f1TempLabel     = wx.StaticText(self.livePanel, label='Furnace 1 Temp      :\tNULL')
		self.f1SetPointLabel = wx.StaticText(self.livePanel, label='Furnace 1 Set Point :\tNULL')
		self.f1UpRampLabel   = wx.StaticText(self.livePanel, label='Furnace 1 Up Ramp   :\tNULL')
		self.f1DownRampLabel = wx.StaticText(self.livePanel, label='Furnace 1 Down Ramp :\tNULL')
		
		self.f2TempLabel     = wx.StaticText(self.livePanel, label='Furnace 2 Temp      :\tNULL')
		self.f2SetPointLabel = wx.StaticText(self.livePanel, label='Furnace 2 Set Point :\tNULL')
		self.f2UpRampLabel   = wx.StaticText(self.livePanel, label='Furnace 2 Up Ramp   :\tNULL')
		self.f2DownRampLabel = wx.StaticText(self.livePanel, label='Furnace 2 Down Ramp :\tNULL')
		
		sizer.Add(self.f1TempLabel)
		sizer.Add(self.f1SetPointLabel)
		sizer.Add(self.f1UpRampLabel)
		sizer.Add(self.f1DownRampLabel)
		sizer.Add(self.f2TempLabel)
		sizer.Add(self.f2SetPointLabel)
		sizer.Add(self.f2UpRampLabel)
		sizer.Add(self.f2DownRampLabel)
		
		# Bind timers 
		self.Bind(wx.EVT_TIMER, self.onRedrawTemps, self.redrawTemps)
		self.Bind(wx.EVT_TIMER, self.onRedrawSettings, self.redrawSettings)
		
		self.SetSizer(sizer)
			
	def onRedrawTemps(self, event):
		self.f1TempLabel.SetLabel('Furnace 1 Temp:\t'+str(util.getFurnace1Temp()))
		self.f2TempLabel.SetLabel('Furnace 2 Temp:\t'+str(util.getFurnace2Temp()))	

	def onRedrawSettings(self, event):
		self.f1SetPointLabel.SetLabel('Furnace 1 Set Point   :\t'+str(util.getFurance1SetPoint()))
		self.f1UpRampLabel.SetLabel('Furnace 1 Up Ramp       :\t'+str(util.getFurnace1UpRamp()))
		self.f1DownRampLabel.SetLabel('Furnace 1 Down Ramp   :\t'+str(util.getFurnace1DownRamp()))
		
		self.f2SetPointLabel.SetLabel('Furnace 2 Set Point   :\t'+str(util.getFurnace2SetPoint()))
		self.f2UpRampLabel.SetLabel('Furnace 2 Up Ramp       :\t'+str(util.getFurnace2UpRamp()))
		self.f2DownRampLabel.SetLabel('Furnace 2 Down Ramp   :\t'+str(util.getFurnace2DownRamp()))		



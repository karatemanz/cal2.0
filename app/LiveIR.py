import util as util
import wx
import wx.aui as aui
import wx.lib.intctrl as ic
import wx.lib.scrolledpanel as sp


# Initial harness to run the simulation in a seperate frame to avoid locking up the main GUI during simulations
class LiveIRFrame(wx.Frame):

	def __init__(self):
		
		wx.Frame.__init__(self,None, title= 'Live IR Sensor Readings', size=(600, 500))
		self.Centre()
		self.livePanel = wx.Panel(self)
		
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.redrawTemps = wx.Timer(self)
		self.redrawTemps.Start(1000)
		
		self.titleLabel = wx.StaticText(self.livePanel, label='Furnace 1 and 2 Live Status Monitor')
		
		self.f1Sample = wx.StaticText(self.livePanel, label='Furnace 1 Sample Temp :\tNULL')
		self.cSample  = wx.StaticText(self.livePanel, label='Cooling Sample Temp   :\tNULL')
		self.f2Sample = wx.StaticText(self.livePanel, label='Furnace 2 Sample Temp :\tNULL')

		sizer.Add(self.f1Sample)
		sizer.Add(self.cSample)
		sizer.Add(self.f2Sample)
				
		# Bind timers 
		self.Bind(wx.EVT_TIMER, self.onRedrawTemps, self.redrawTemps)
		
		self.SetSizer(sizer)
			
	def onRedrawTemps(self, event):
		self.f1Sample.SetLabel('Furnace 1 Temp :\t'+str(util.read3208(util.Furnace_1)))
		self.f1Sample.SetLabel('Cooling Temp   :\t'+str(util.read3208(util.CoolChannel)))
		self.f2Sample.SetLabel('Furnace 2 Temp :\t'+str(util.read3208(util.Furnace_2)))	

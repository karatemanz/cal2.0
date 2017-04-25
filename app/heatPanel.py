import wx
import os
import time
import datetime
import matplotlib
matplotlib.use('WXAgg')
import numpy as np
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
import pylab
import mygrid
import pandas as pd

class TabPanel(wx.Panel):

	def __init__(self, parent):
		wx.Panel.__init__(self, parent=parent, id=wx.ID_ANY)
		sizer = wx.BoxSizer(wx.VERTICAL)
		
		self.date = []
		today = datetime.date.today()
		self.date.append(today)
		self.date = str(self.date[0])
		self.gridIndex = 0
		self.maxfx = 0
		
		self.estTimes = [0]
		self.estTemps = [0]
		self.dataTimes = [0]
		self.dataTemps = [0]
		
		self.initPlot()
				
		self.canvas = FigureCanvas(self, -1, self.fig)
		self.dataGrid = mygrid.MyGrid(self)
		
		sizer.Add(self.canvas)
		sizer.Add(self.dataGrid)
		self.SetSizer(sizer)
		self.canvas.draw()
												
	def initPlot(self):
		
		# Set min values
		self.xmin = 0
		self.ymin = 0
		self.xmax = 0
		self.ymax = 0
		self.xemax = 0
		self.yemax = 0
		self.xdmax = 0
		self.ydmax = 0
		
		self.dpi = 100
		self.fig = Figure((10, 5), dpi=self.dpi)
		
		# Initialize Furnace 1 Graph
		self.axeE = self.fig.add_subplot(1,1,1)
		self.axeE.set_axis_bgcolor('white')
		self.axeE.set_title('Furnace 1 Simulation Plot')
		self.axeE.set_xlabel('Time (s)')
		self.axeE.set_ylabel('Temperature (C)')
		self.axeE.grid(True, color='gray')
		
		# Default Initialized X, Y Bounds
		self.axeE.set_xbound(lower=0, upper=30)
		self.axeE.set_ybound(lower=0, upper=1000)
			
		# Initialize Simulation Estimate Data
		self.plotSimEst = self.axeE.plot(
			self.estTemps,
			linewidth = 1,
			color = ('blue'),
			label = 'estimate',
			)[0]
		
		self.axeD = self.axeE.twinx()
		
		# Initialize Simulation Sensor Data
		self.plotData = self.axeD.plot(
			self.dataTemps,
			linewidth = 1,
			color = ('green'),
			label = 'data',
			)[0]
			
		# Initialize estimate plot
		self.plotSimEst.set_xdata([])
		self.plotSimEst.set_ydata([])		
			
		# Initialize data plot
		self.plotData.set_xdata([])
		self.plotData.set_ydata([])		
			
		
	# draw the plot based on updated data	
	def drawPlot(self, times, temps):
		
		if len(times) > 0 and len(temps) > 0:
		
			xmin = 0
			ymin = 0
			# Get Data Values From Simulation Execution
			xmax = max(times) + 10
			ymax = max(temps) + 100	

			self.axeD.set_xbound(lower=xmin, upper=xmax)
			self.axeD.set_ybound(lower=ymin, upper=ymax)
																
			# Plot collected simulation data
			self.plotData.set_xdata(times)
			self.plotData.set_ydata(temps)
			
			# Record to file, and plot values from file
			self.canvas.draw()
		
	def drawEstPlot(self, times, temps):
			
		if len(times) > 0 and len(temps) > 0:	
			
			# Get Estimate Values From Cycle Settings
			xmin = 0
			ymin = 0
			xmax = max(times) + 10
			ymax = max(temps) + 100
				
			# Set Estimate Bounds
			self.axeE.set_xbound(lower=xmin, upper=xmax)
			self.axeE.set_ybound(lower=ymin, upper=ymax)
			
			# Plot estimation values		
			self.plotSimEst.set_xdata(times)
			self.plotSimEst.set_ydata(temps)		
			
			# Record to file, and plot values from file
			self.canvas.draw()	
			
	
	# samples saved: can use graphViewer.py in /results to view data graphically after simulation		
	def recordData(self, fileName):
		 			 		 				 	
		commonName = "/home/pi/Desktop/CAL/cal2.0/app/results/"+fileName
		filename = commonName+'-['+self.date+']-Heating'+'.csv'
									
		data = { 'time' : self.plotData.get_xdata(), 'temp': self.plotData.get_ydata() }			
		
		df = pd.DataFrame(data, columns=['time', 'temp'])
		
		if not os.path.isfile(filename):	
			df.to_csv(filename, encoding='utf-8-sig', index=False)
		else:
			df.to_csv(filename, encoding='utf-8-sig', index=False, header=False, mode='w')
			
	# Not used: for personal interest and future use					
	def plotFromFile(self, fileName):
		
		if len(fileName) > 0:
			
			tempOff = 100
			timeOff = 10

			commonName = "/home/pi/Desktop/CAL/cal2.0/app/results/"+fileName
			filename = commonName+'-Heating'+'.csv'
			df = pd.read_csv(filename, names=['time', 'temp'], encoding='utf-8-sig')
		 
			times = [float(x) for x in df.time.tolist()]
			temps = [float(x) for x in df.temp.tolist()]
			
			self.plotData.set_xdata(times)
			self.plotData.set_ydata(temps)
			
			self.axeD.set_xbound(lower=self.xmin, upper=max(self.plotData.get_xdata()) + timeOff)
			self.axeD.set_ybound(lower=self.ymin, upper=max(self.plotData.get_ydata()) + tempOff)
			
			self.canvas.draw()
			
	# plot individual point on the graph	
	def plotPoint(self, x, y):
		
		tempOff = 100
		timeOff = 10
		
		# Plot point to existing points
		self.plotData.set_xdata(np.append(self.plotData.get_xdata(), x))
		self.plotData.set_ydata(np.append(self.plotData.get_ydata(), y))
		
		# Update bounds based on point
		self.axeD.set_xbound(lower=self.xmin, upper=max(self.plotData.get_xdata()) + timeOff)
		self.axeD.set_ybound(lower=self.ymin, upper=max(self.plotData.get_ydata()) + tempOff)
		
		self.canvas.draw()
	
	def resetPlot(self):
		self.plotData.set_xdata([])
		self.plotData.set_ydata([])	
		
	# add a data point to the grid	
	def addDataToGrid(self, datax, datay):
		
		for i in range(len(datax)):
			self.addRowToGrid(datax[i], datay[i])
				
	# Not used: because not in thread * massive amounts of data points + 4 plots =	takes forever to compute and usually just freezes up
	def addRowToGrid(self, x, y):
		
		self.dataGrid.grid.AppendRows(numRows=1, updateLabels=True)	
		self.dataGrid.grid.SetCellValue(self.gridIndex, 0, str(x))
		self.dataGrid.grid.SetCellValue(self.gridIndex, 1, str(y))

		self.dataGrid.grid.SetCellAlignment(self.gridIndex,0,wx.ALIGN_CENTER,wx.ALIGN_CENTER) 
		self.dataGrid.grid.SetCellAlignment(self.gridIndex,1,wx.ALIGN_CENTER,wx.ALIGN_CENTER)
		self.dataGrid.grid.ForceRefresh()
		
		self.gridIndex += 1
		
	def resetGrid(self):
		self.dataGrid.grid.ClearGrid()
		self.gridIndex = 0	
		
	def reset(self):
		self.resetPlot()
		self.resetGrid()
		self.canvas.draw()
	
	def resetEst(self):
		self.plotSimEst.set_xdata([])
		self.plotSimEst.set_ydata([])
		self.canvas.draw()
		
							
class DemoFrame(wx.Frame):
	def __init__(self):
		wx.Frame.__init__(self, None, wx.ID_ANY, "Heating Graph")
		panel = TabPanel(self)		
		self.Show()
        
#----------------------------------------------------------------------
if __name__ == "__main__":
    app = wx.App()
    frame = DemoFrame()
    app.MainLoop()



import matplotlib.pyplot as plt
import pandas as pd

from Tkinter import Tk
from tkFileDialog import askopenfilename


def onKeyPress(event):
	
	plt.clf()
	
	filename = askopenfilename()

	df = pd.read_csv(filename, names=['time', 'temp'], encoding='utf-8-sig')

	if len(filename) > 0:
		
		print df.head()

		time = [float(x) for x in df.time[1:]]
		temp = [float(y) for y in df.temp[1:]]

		plt.plot(time, temp)

		plt.show() 

def onClose(event):
	plt.close()
	Tk().close()
	

print "Please select a *.csv file to view it's contents graphically"
print "Clicking in the Tkinter window and pressing the 'n' key will allow you to view another dataset"
# Choose a graph to view
Tk().withdraw()
Tk().bind('n', onKeyPress)
filename = askopenfilename()

if len(filename) > 0:

	df = pd.read_csv(filename, names=['time', 'temp'], encoding='utf-8-sig')

	print df.head()

	time = [float(x) for x in df.time[1:]]
	temp = [float(y) for y in df.temp[1:]]

	plt.plot(time, temp)

	plt.show() 




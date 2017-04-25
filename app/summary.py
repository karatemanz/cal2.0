# ---------------------------------------------------------------------------------------------
#  Summary reading and writing of the simulation definition of a simulation
# ---------------------------------------------------------------------------------------------

import os
import pandas as pd
import numpy as np
from cal import *
import util

date = []
today = datetime.date.today()
date.append(today)
date = str(date[0])

def writeSummary(fileName, stages, startTemps, endTemps, setRates):

	commonName = "/home/pi/Desktop/CAL/cal2.0/app/results/"+fileName
	filename = commonName+'-['+date+']-Summary'+'.csv'
												
	stages     = [x for x in stages if x is not None]
	startTemps = [x for x in startTemps if x is not None]	
	endTemps   = [x for x in endTemps if x is not None]	
	setRates   = [x for x in setRates if x is not None]
								
	data = { 'stage' : stages, 'startTemp' : startTemps, 'endTemp' : endTemps, 'rates' : setRates }			
	
	df = pd.DataFrame(data, columns=['stage', 'startTemp', 'endTemp', 'rates'])
	
	if not os.path.isfile(filename):	
		df.to_csv(filename, encoding='utf-8-sig', index=False)
	else:
		df.to_csv(filename, encoding='utf-8-sig', index=False, header=False, mode='w')	

def importSummary(fileName):
	
	commonName = "/home/pi/Desktop/CAL/cal2.0/app/results/"+fileName
	filename = commonName+'-Summary'+'.csv'
	
	df = pd.read_csv(filename, names=['stage', 'startTemp', 'endTemp', 'rates'], encoding='utf-8-sig')
	 	 
	stages		= [int(x) for x in df.stage.tolist()]
	startTemps  = [float(x) for x in df.startTemp.tolist()]
	endTemps    = [float(x) for x in df.endTemp.tolist()]
	setRates    = [float(x) for x in df.rates.tolist()]	
		
	return stages, startTemps, endTemps, setRates	

#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This file contains functions used to analyse data sets for a single
# test case.

import sys
import argparse
import glob
import os

from TSVContainer import TSVContainer
from PrintFuncs import *
import pandas as pd  # Data manipulation and analysis
from StatisticsFunctions import StatisticsFunctions as sf

RESULTS_SUBDIRNAME = "Auswertung/Ergebnisse"
EVAL_PERIODS = "EvaluationPeriods.tsv"


class CaseResults:
	def __init__(self):
		self.score = 0
		self.norms = dict()
		
		self.simQbadge = 0 # means failed
		
		self.ToolID = ""
		self.TestCase = ""
		self.Variable = ""
		self.ErrorCode = -10 # no data/dataset broken


def appendErrorResults(tsvData, testCaseName, toolID, errorCode, variables):
	cr = CaseResults()
	cr.TestCase = testCaseName
	cr.ToolID = toolID
	cr.ErrorCode = errorCode
	for v in variables:
		cr.Variable = v
		tsvData.append(cr)


def listsEqual(list1, list2):
	if len(list1) != len(list2):
		return False
	for i in range(len(list1)):
		if list1[i] != list2[i]:
			return False
	return True


def evaluateVariableResults(variable, timeColumn, refData, testData, start, end, weightFactors):
	"""
	Performance difference calculation between variable data sets.
	
	we use different statistical metrics to perform deep comparisions 
	of the different datasets.
	
	"""
	printNotification("    {}".format(variable))
	cr = CaseResults()
	
	try:
		
		# We first convert our data to pandas
		pdTime = pd.DataFrame(data=pd.date_range(start="2018-01-01", periods=len(timeColumn), freq="H"), index=timeColumn, columns=["Date and Time"])
		pdData = pd.DataFrame(data=testData, index=timeColumn, columns=["Data"])
		pdRef = pd.DataFrame(data=refData, index=timeColumn, columns=["Data"])
		
		# We only use data between out start and end point
		pdTime = pdTime.loc[start:end]
		pdData = pdData.loc[start:end]
		pdRef = pdRef.loc[start:end]
		
		# we evaluate the results		
		cr.norms['Maximum'] = sf.function_Maximum(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['Minimum'] = sf.function_Minimum(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['Average'] = sf.function_Average(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		
		cr.norms['CVRMSE'] = sf.function_CVRMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['Daily Amplitude CVRMSE'] = sf.function_Daily_Amplitude_CVRMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['MBE'] = sf.function_MBE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['RMSEIQR'] = sf.function_RMSEIQR(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['MSE'] = sf.function_MSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['NMBE'] = sf.function_NMBE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['NRMSE'] = sf.function_NRMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['RMSE'] = sf.function_RMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['RMSLE'] = sf.function_RMSLE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['R squared coeff determination'] = sf.function_R_squared_coeff_determination(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		cr.norms['std dev'] = sf.function_std_dev(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
		
		
	except IOError as e:
		print(e)
		print("Cannot create statistical evaluation for variable %1".format(variable))
		exit(1)		

	# TODO : Wichtung
	if(abs(cr.norms['Average']) < 1e-4):
		cr.score = 0		# prevent division by zero error
	else:
		cr.score = ( weightFactors.get('CVRMSE', 0) * ( 100.0 - cr.norms['CVRMSE'] ) +  		# in %
			     weightFactors.get('Daily Amplitude CVRMSE', 0) * ( 100.0 - cr.norms['Daily Amplitude CVRMSE'] ) + 	# in % 
			     weightFactors.get('MBE', 0) * ( 100.0 - 100.0*cr.norms['MBE'] / cr.norms['Average']) + 
			     weightFactors.get('RMSEIQR', 0) * ( 100.0 - cr.norms['RMSEIQR'] ) + 		# in %
			     weightFactors.get('MSE', 0) * ( 100.0 - 100*cr.norms['MSE'] / cr.norms['Average']) + 
			     weightFactors.get('NMBE', 0) * ( 100.0 - cr.norms['NMBE'] ) + 
			     weightFactors.get('NRMSE', 0) * ( 100.0 - cr.norms['NRMSE'] ) + 
			     weightFactors.get('RMSE', 0) * ( 100.0 - 100.0*cr.norms['RMSE'] / cr.norms['Average']) + 
			     weightFactors.get('RMSLE', 0) * ( 100.0 - cr.norms['RMSLE'] / cr.norms['Average']) + 
			     weightFactors.get('R squared coeff determination', 0)*( 100.0 - cr.norms['R squared coeff determination'] / cr.norms['Average']) + 
			     weightFactors.get('std dev', 0)*( 100.0 - cr.norms['std dev'] / cr.norms['Average']) ) / weightFactors['Sum'] 
	
	# scoring caluclation --> >95% : Gold | >90% : Silver | >80% : Bronze
	badge = 0
	if(cr.score>95):
		badge = 1
	elif(cr.score>90):
		badge = 2
	elif(cr.score>80):
		badge = 3
	# now set the final SimQuality Badge 
	cr.simQbadge = badge
	
	return cr


# all the data is stored in a dictionary with tool-specific data
def processDirectory(path, weightFactors):
	"""
	Processes a test case directory, i.e. path = "data/TF03-Waermeleitung".
	It then reads data from the subdirectory 'Auswertung/Ergebnisse' and
	calculates the validation score.
	
	Returns a CaseResults object with data for all test variables. 
	'None' indicates entirely invalid/missing test data or reference data.
	"""

	# test case name
	testCaseName = os.path.split(path)[1]
	testCaseName = testCaseName[2:]
	

	# result dir exists?
	tsvPath = os.path.join(path, RESULTS_SUBDIRNAME)

	if not os.path.exists(tsvPath):
		printError("Missing test result directory '{}'.".format(tsvPath))
		return None # None indicates entirely invalid/missing test data.
	

	tsvFiles = [o for o in os.listdir(tsvPath) if o.endswith("tsv")]
	if not "Reference.tsv" in tsvFiles:
		printError("Missing 'Reference.tsv' file.")
		return None
	if not "EvaluationPeriods.tsv" in tsvFiles:
		printError("Missing 'EvaluationPeriods.tsv' file.")
		return None
	tsvFiles = sorted(tsvFiles)
	
	# read evaluation periods
	evalData = TSVContainer()
	evalData.readAsStrings(os.path.join(tsvPath, "EvaluationPeriods.tsv"))
	if True in evalData.emptyColumn:
		printError("'EvaluationPeriods.tsv' contains empty columns.")
		return None

	
	# read reference file
	refData = TSVContainer()
	refData.readAsStrings(os.path.join(tsvPath, "Reference.tsv") )
	if True in refData.emptyColumn:
		printError("'Reference.tsv' contains empty columns.")
		return None
	if not refData.convert2Double():
		printError("'Reference.tsv' contains invalid numbers.")
		return None
	
	# extract variable names
	variables = []
	rawVariables = []
	for v in refData.headers[1:]:
		rawVariables.append(v)
		# remove unit and optional '(mean)' identifier
		p = v.find("(mean)")
		if p == -1:
			p = v.find("[")
		if p == -1:
			print("Missing unit in header label '{}' of 'Reference.tsv'".format(v))
			return None
		v = v[0:p].strip()
		variables.append(v)
		printNotification("  {}".format(v))
		
	# extract variable names
	evaluationVariables = []
	for e in evalData.data[0]:
		evaluationVariables.append(e)
		printNotification("  {}".format(e))		

	# now read in all the reference files, collect the variable headers and write out the collective file
	tsvData = []
	for dataFile in tsvFiles:
		# special handling of reference data files needed only for visualization
		if dataFile.startswith("Reference"):
			continue
		
		if dataFile.startswith("EvaluationPeriods"):
			continue		
		
		printNotification("Reading '{}'.".format(dataFile))
		toolID = dataFile[0:-4] # strip tsv
		tsv = TSVContainer()
		tsv.readAsStrings(os.path.join(tsvPath, dataFile))
		if True in tsv.emptyColumn:
			printError("'{}' contains empty columns, skipped.".format(dataFile))
			appendErrorResults(tsvData, testCaseName, toolID, -10, variables)
			continue
		# check if header line is exactly correct
		#if not listsEqual(refData.headers, tsv.headers):
			#printError("'{}''s header doesn't match header of 'Reference.tsv'".format(dataFile))
			#appendErrorResults(tsvData, testCaseName, toolID, -9, variables)
			#continue
		
		# if not all data is provieded by a tool we only want to skip the specific variable
		for header in tsv.headers:
			if header not in refData.headers:
				printError("'{}''s header '{}' is not part of the reference header".format(dataFile, header))
				continue
		
		# number of cols
		#if len(refData.data) != len(tsv.data):
			#printError("'{}''s mismatching number of columns in file compared to 'Reference.tsv'".format(dataFile))
			#appendErrorResults(tsvData, testCaseName, toolID, -8, variables)
			#continue

		if not tsv.convert2Double():
			printError("Data file contains invalid numbers.")
			appendErrorResults(tsvData, testCaseName, toolID, -7, variables)
			continue
		
		# process all variables
		for i in range(len(variables)):
			# call function to generate and evaluate all norms for the given variable
			# we provide time column, reference data column and value column, also parameter set for norm calculation
			# we get a variable-specific score stored in CaseResults object
			if not rawVariables[i] in tsv.headers:
				printError("'{}''s does not contain the variable {} and will be skipped.".format(dataFile, variables[i]))
				continue
			
			# check if data even exists
			if i > len(tsv.data) :
				printError("'{}''s columns exceed number of columns of 'Reference.tsv'".format(dataFile))
				appendErrorResults(tsvData, testCaseName, toolID, -11, variables)
				break					

			# number of rows
			if len(refData.data[i]) != len(tsv.data[i]):
				printError("'{}''s mismatching number of rows ({}) in file compared to 'Reference.tsv' ({})".format(dataFile, len(tsv.data[i]), len(refData.data[i]) ) )
				appendErrorResults(tsvData, testCaseName, toolID, -12, variables)
				continue
			

			if not variables[i] in evaluationVariables:
				printError("'EvaluationPeriods.tsv' does not contain the variable '{}'".format(variables[i]))
				continue
			
			for j in range(len(evaluationVariables)):
				if variables[i] == evaluationVariables[j]:
					start = int(evalData.data[1][j])
					end = int(evalData.data[2][j])
					break
			
			if end < start:
				printError("Evaluation End Point ({}) has to be after start point ({}).".format(end, start))
				continue
						
			if end > len(refData.data[0]):
				printError("Evaluation End Point ({}) is bigger then row number of reference results.".format(end, len(refData.data[0])))
				continue				
			
			cr = evaluateVariableResults(variables[i], refData.data[0], refData.data[i+1], tsv.data[i+1], start, end, weightFactors)
			cr.TestCase = testCaseName
			cr.ToolID = toolID
			cr.Variable = variables[i]
			cr.ErrorCode = 0
			tsvData.append(cr)

	return tsvData

#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Script to automatically process all simquality test result directories
# and generate a score file.
#
# Script is expected to be run from within the 'data' directory.

import os
import sys

from TSVContainer import TSVContainer
from ProcessDirectory import processDirectory
from colorama import *
from PrintFuncs import *

BADGES = {
	0: "Failed",
	1: "Gold",
	2: "Silver",
	3: "Bronze"
}

def readWeightFactors():
	# read weight factors
	# CVRMSE	Daily Amplitude CVRMSE	MBE	RMSEIQR	MSE	NMBE	NRMSE	RMSE	RMSLE	R² coefficient determination	std dev
	try:
		weightFactorsTSV = TSVContainer()
		weightFactorsTSV.readAsStrings(os.path.join(os.getcwd(), "WeightFactors.tsv"))
	except RuntimeError as e:
		print(e)
		print(f"At least one weight factor has to be specified in 'WeightFactors.tsv'.")
		exit (1)
	
	weightFactors = dict()
	
	for i in range(len(weightFactorsTSV.data[0])):
		weightFactors[weightFactorsTSV.data[0][i]] = int(weightFactorsTSV.data[1][i])
		
	
	weightFactors['Sum'] = sum(map(int, weightFactorsTSV.data[1])) # convert to int and then sum it up
		
	return weightFactors


# ---*** main ***---


# Create results file
try:
	fobj = open("Results.tsv", "w")
except IOError as e:
	print(e)
	print("Cannot create 'Results.tsv' file")
	exit(1)

# Create log file
oldStdout = sys.stdout
try:
	log = open("Log.txt", "w")
except IOError as e:
	print(e)
	print("Cannot create 'Log.txt' file")
	exit(1)

# redirect outputs to log
sys.stdout = log

# initialize colored console output
init()

weightFactors = readWeightFactors()

# create dictionary for test case results
testresults = dict()

# process all subdirectories of `AP4` (i.e. test cases)
subdirs = os.listdir(os.curdir)

# process all subdirectory starting with TF
for sd in subdirs:
	if len(sd) > 4 and sd.startswith("TF"):
		# extract next two digits and try to convert to a number
		try:
			testCaseNumber = int(sd[2:3])
		except:
			printError("Malformed directory name: {}".format(sd))
			continue
		printNotification("\n################################################\n")
		printNotification("Processing directory '{}'".format(sd))
		testresults[sd] = processDirectory( os.path.join(os.getcwd(), sd), weightFactors )

# dump test results into file

fobj.write("Testfall\tToolID\tVariable\tFehlercode\tMax\tMin\tAverage\tCVRMSE\tDaily Amplitude CVRMSE\tMBE\tRMSEIQR\tMSE\tNMBE\tNRMSE\tRMSE\tRMSLE\tR² coefficient determination\tstd dev\tSimQuality-Score\tSimQ-Einordnung\n")

testcases = sorted(testresults.keys())

for testcase in testcases:
	testData = testresults[testcase]
	# skip test cases with missing/invalid 'Reference.tsv'
	if testData == None:
		continue
	for td in testData:
		resText = "{}\t{}\t{}\t{}\t".format(td.TestCase, td.ToolID, td.Variable, td.ErrorCode)
		for key in td.norms:
			resText = resText + "{}\t".format(td.norms[key])
		resText = resText + "{}\t".format(td.score)
		resText = resText + "{}\n".format(BADGES.get(td.simQbadge))
		fobj.write(resText)
		
sys.stdout = oldStdout

fobj.close()
del fobj
log.close()
del log

printNotification("\n################################################\n")
printNotification("Done.")

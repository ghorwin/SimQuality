#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This script processes all data files of a single test case.
# The actual work is done in class TestCase.
# 
# The main script expects the path to the working directory, or
# uses the current working directory, if path is missing.
#

import sys
import argparse
import glob
import os

from TSVContainer import TSVContainer
from PrintFuncs import *

RESULTS_SUBDIRNAME = "Auswertung/Ergebnisse"


class CaseResults:
	def __init__(self):
		self.score = 0
		self.norms = []
		self.norms.append(0)
		self.norms.append(0)
		self.norms.append(0)
		self.norms.append(0)
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


def evaluateVariableResults(variable, timeColumn, refData, testData):
	"""Performance difference calculation between variable data sets."""
	printNotification("    {}".format(variable))
	cr = CaseResults()
	
	# TODO Stephan
	cr.score = 15
	return cr


# all the data is stored in a dictionary with tool-specific data
def processDirectory(path):
	"""
	Processes a test case directory, i.e. reads data from 'Auswertung/Ergebnisse' and
	calculates score.
	
	Returns a table with data for all test cases and variables. 'None' indicates entirely invalid/missing test data.
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
	tsvFiles = sorted(tsvFiles)

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
	for v in refData.headers[1:]:
		# remove unit and optional '(mean)' identifier
		p = v.find("(mean)")
		if p == -1:
			p = v.find("[")
		if p == -1:
			print("Missing unit in header label '{}' of 'Reference.tsv'".format(v))
			return None
		v = v[0:p]
		variables.append(v)
		printNotification("  {}".format(v))


	# now read in all the reference files, collect the variable headers and write out the collective file
	tsvData = []
	for dataFile in tsvFiles:
		# special handling of reference data files needed only for visualization
		if dataFile.startswith("Reference_"):
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
		if not listsEqual(refData.headers, tsv.headers):
			printError("'{}''s header doesn't match header of 'Reference.tsv'".format(dataFile))
			appendErrorResults(tsvData, testCaseName, toolID, -9, variables)
			continue
		
		# number of rows
		if len(refData.data) != len(tsv.data):
			printError("'{}''s mismatching number of rows in file compared to 'Reference.tsv'".format(dataFile))
			appendErrorResults(tsvData, testCaseName, toolID, -8, variables)
			continue

		if not tsv.convert2Double():
			printError("Data file contains invalid numbers.")
			appendErrorResults(tsvData, testCaseName, toolID, -7, variables)
			continue
		
		# process all variables
		for i in range(len(variables)):
			# call function to generate and evaluate all norms for the given variable
			# we provide time column, reference data column and value column, also parameter set for norm calculation
			# we get a variable-specific score stored in CaseResults object
			
			cr = evaluateVariableResults(variables[i], refData.data[0], refData.data[i+1], tsv.data[i+1])
			cr.TestCase = testCaseName
			cr.ToolID = toolID
			cr.ErrorCode = 0
			tsvData.append(cr)

	return tsvData
#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Script to automatically process all simquality test result directories
# and generate a score file.
#
# Script is expected to be run from within the 'data' directory.

import os

from ProcessDirectory import processDirectory
from colorama import *
from PrintFuncs import *

BADGES = {
	0: "Failed",
	1: "Gold",
	2: "Silver",
	3: "Bronze"
}


# ---*** main ***---

# initialize colored console output
init()

try:
	fobj = open("Results.tsv", 'w')
except IOError as e:
	print(e)
	print("Cannot create 'Results.tsv' file")
	exit(1)

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
		printNotification("Processing directory '{}'".format(sd))
		testresults[sd] = processDirectory( os.path.join(os.getcwd(), sd) )

# dump test results into file
fobj.write("Testfall\tToolID\tVariable\tFehlercode\tNorm1\tNorm2\tNorm3\tNorm4\tSimQuality-Score\tSimQ-Einordnung\n")

testcases = sorted(testresults.keys())


for testcase in testcases:
	testData = testresults[testcase]
	# skip test cases with missing/invalid 'Reference.tsv'
	if testData == None:
		continue
	for td in testData:
		resText = "{}\t{}\t{}\t{}\t".format(td.TestCase, td.ToolID, td.Variable, td.ErrorCode)
		for n in td.norms:
			resText = resText + "{}\t".format(n)
		resText = resText + "{}\t".format(td.score)
		resText = resText + "{}\n".format(BADGES.get(td.simQbadge))
		fobj.write(resText)

fobj.close()
del fobj

printNotification("Done.")

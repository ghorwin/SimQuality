#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Script to automatically process all simquality test result directories
# and generate a score file.
#
# Script is expected to be run from within the 'data' directory.

import os
import sys
import plotly.graph_objects as go
import pandas as pd

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

TOOLCOLORS = {
    "Reference": "#000000",
    "ETU": "#8ae234",
    "IDAICE": "#e50c0c",
    "NANDRAD": "#ffc120",
    "NANDRAD2": "#ffc120",
    "Aixlib": "#7c00bf",
    "TRNSYS": "#0369a3",
    "TAS": "#ffd74c",
    "THERAKLES": "#d36118"
}

LINESTYLES = {
    "Reference": "markers",
    "ETU": "lines",
    "IDAICE": "lines",
    "NANDRAD": "lines",
    "NANDRAD2": "lines",
    "Aixlib": "lines",
    "TRNSYS": "lines",
    "TAS": "lines",
    "THERAKLES": "lines"
}

def scoreCalculation():
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
            testresults[sd] = processDirectory(os.path.join(os.getcwd(), sd))

    # dump test results into file

    fobj.write(
        "Testfall\tToolID\tVariable\tFehlercode\tMax\tMin\tAverage\tCVRMSE\tDaily Amplitude CVRMSE\tMBE\tRMSEIQR\tMSE\tNMBE\tNRMSE\tRMSE\tRMSLE\tR² coefficient determination\tstd dev\tSimQuality-Score\tSimQ-Einordnung\n")

    printNotification("\n################################################\n")
    printNotification("Done.")


# ---*** main ***---
if __name__ == "__main__":
	scoreCalculation()
	exit(1)

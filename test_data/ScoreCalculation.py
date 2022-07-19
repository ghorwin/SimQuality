#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Script to automatically process all simquality test result directories
# and generate a score file.
#
# Script is expected to be run from within the 'data' directory.

import os
import sys

sys.path.append("../scripts")

print(os.path.join(os.getcwd(), "../scripts"))

import plotly.graph_objects as go
import pandas as pd
import feather
import shutil

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

def scoreCalculation():
    # Create results file
    try:
        fobj = open("../dash_data/Results.tsv", "w", encoding="utf-8")
    except IOError as e:
        print(e)
        print("Cannot create 'Results.tsv' file")
        exit(1)

    # Create log file
    # oldStdout = sys.stdout
    # try:
    #     log = open("Log.txt", "w")
    # except IOError as e:
    #     print(e)
    #     print("Cannot create 'Log.txt' file")
    #     exit(1)

    # redirect outputs to log
    # initialize colored console output
    init()

    # create dictionary for test case results
    testresults = dict()

    # process all subdirectories of `AP4` (i.e. test cases)
    subdirs = os.listdir(os.curdir)
    try:
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
    except Exception as e:
        fobj.close()
        del fobj
        printError(str(e))
        raise Exception(f"Could not process data in directory {sd}")

    # dump test results into file

    fobj.write(
        "Test Case\tVariable\tToolID\tTool Name\tVersion\tUnit\tEditor\tFehlercode\t"
        "Average [-]\tCVRMSE [%]\tDaily Amplitude CVRMSE [%]\tMBE\tMSE [%]\tMax Difference [-]\tMaximum [-]\tMinimum [-]\tNMBE [%]\tNRMSE [%]\tR squared [-]\tRMSE [%]\tRMSEIQR [%]\tRMSLE [%]\tstd dev [-]"
        "\tReference\tSimQ-Score [%]\tSimQ-Rating\n"
    )

    testcases = sorted(testresults.keys())

    colors = dict()

    for testcase in testcases:
        testData = testresults[testcase]
        # skip test cases with missing/invalid 'Reference.tsv'
        if testData == None:
            continue
        for td in testData:
            resText = "{}\t{}\t{}\t{}\t{}\t{}\t{}\t{}\t".format(td.TestCase, td.Variable, td.ToolID, td.DisplayName,
                                                            td.Version, td.Unit, td.Editor, td.ErrorCode)

            sortedKeys = sorted(td.norms.keys())

            for n in sortedKeys:
                if n == "Sum":
                    continue
                resText = resText + "{}\t".format(td.norms[n])
            resText = resText + "{}\t".format(td.Reference)
            resText = resText + "{}\t".format(td.score)
            resText = resText + "{}\n".format(BADGES.get(td.simQbadge))
            fobj.write(resText)

            colors[td.ToolID] = td.DisplayColor

    fobj.close()
    del fobj
    printNotification("\n################################################\n")

    printNotification("\nConvert data for SimQuality Dashboard\n")

    #### Convert to website ####
    # pandaResults = dict()
    # convertToPandas()

    dashDir = "../dash_data/"

    for testcase in testresults.keys():
        if testresults[testcase] is None:
            continue

        printNotification(f"\n------------------------------------\n")
        printNotification(f"Converting all data for test Case {testcase}")

        path1 = os.path.join(testCaseDir, testcase, "WeightFactors.tsv")
        path2 = os.path.join(dashDir, testcase, "WeightFactors.tsv")

        shutil.copy2(path1, path2)

        for var in testresults[testcase]:
            if var.Data.empty:
                continue
            testCaseDir = os.path.join(dashDir, testcase)
            if not os.path.exists(testCaseDir):
                os.mkdir(testCaseDir)
            variableDir = os.path.join(testCaseDir, var.Variable)
            if not os.path.exists(variableDir):
                os.mkdir(variableDir)
            file = os.path.join(dashDir, testcase, var.Variable, var.ToolID + ".ftr")
            refFile = os.path.join(dashDir, testcase, var.Variable, "Reference.ftr")
            try:
                df = var.Data.reset_index()
                dfRef = var.RefData.reset_index()
                df.to_feather(file)
                dfRef.to_feather(refFile)
            except Exception as e:
                printError(e)
                printError("Could not convert panda data to feather data.")

    printNotification("\n################################################\n\n")
    printNotification("Done producing evaluation data and dash conversion.")

    #### Convert data dict ####
    try:
        resultFile = "ToolColors.tsv"
        colorDf = pd.DataFrame.from_dict(colors, orient='index')
        colorDf.to_csv(os.path.join(dashDir, resultFile), sep="\t", header=False)
    except Exception as e:
        printError(str(e))
        raise Exception(f"Could not create tool color file {colorDf}.")

# ---*** main ***---
if __name__ == "__main__":
    try:
        scoreCalculation()
    except Exception as e:
        printError(str(e))
        printError("Could not evaluate SimQuality results.")
    exit(1)

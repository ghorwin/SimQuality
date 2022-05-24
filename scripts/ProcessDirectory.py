#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# This file contains functions used to analyse data sets for a single
# test case.

import sys
import argparse
import glob
import os
import pandas as pd  # Data manipulation and analysis
import datetime as dt
from StatisticsFunctions import StatisticsFunctions as sf
import plotly

from TSVContainer import TSVContainer
from PrintFuncs import *

from scripts.PrintFuncs import printError, printNotification

RESULTS_SUBDIRNAME = "result_data"
EVAL_PERIODS = "EvaluationPeriods.tsv"


class CaseResults:
    def __init__(self):
        self.score = 0
        self.norms = dict()

        self.simQbadge = 0  # means failed

        self.ToolID = ""
        self.TestCase = ""
        self.Variable = ""
        self.ErrorCode = -10  # no data/dataset broken
        self.Editor = ""
        self.Version = ""
        self.DisplayName = ""
        self.Unit = ""
        self.Reference = False

        self.Data = pd.DataFrame
        self.RefData = pd.DataFrame


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


def evaluateVariableResults(variable, timeColumnRef, timeColumnData, refData, testData, starts, ends, weightFactors,
                            timeIndicator):
    """
	Performance difference calculation between variable data sets.
	
	we use different statistical metrics to perform deep comparisions 
	of the different datasets.
	
	"""
    printNotification("    {}".format(variable))
    cr = CaseResults()

    pdTime = pd.DataFrame()
    pdRef = pd.DataFrame()
    pdData = pd.DataFrame()

    cr.RefData = pd.DataFrame()

    # initialize all statistical methods in cr.norms
    for key in weightFactors:
        cr.norms[key] = -99

    for i in range(len(starts)):
        start = starts[i]
        end = ends[i]

        # Check if time columns are equal. Some tools cannot produce output in under hourly mannor.
        # For this we are nice and try to convert our reference results.
        if not listsEqual(timeColumnData, timeColumnRef):
            printWarning(f"        Mismatching time columns in Data set file and reference data set.")
            printWarning(f"        Trying to convert reference data set.")

            newTestData = []

            for i in range(len(timeColumnRef)):
                if timeColumnRef[i] not in timeColumnData.index:
                    return cr

                index = timeColumnData.index(timeColumnRef[i])
                newTestData.append(timeColumnData[index])

            # time column data from tool data set is now set for reference data set
            timeColumnData = timeColumnRef
            testData = newTestData

        # We first convert our data to pandas
        try:
            split = 1
            if timeIndicator == "min":
                split = 60

            # Convert all the data to hourly indexes
            start = float(start) / split
            end = float(end) / split

            tempTimeColumnData = [x / split for x in timeColumnData]
            tempTimeColumnRef = [x / split for x in timeColumnRef]

            startDate = dt.datetime(2021, 1, 1) + dt.timedelta(hours=tempTimeColumnData[0])
            pdT = pd.DataFrame(data=pd.date_range(start=startDate, periods=len(tempTimeColumnRef), freq=timeIndicator),
                               index=tempTimeColumnRef, columns=["Date and Time"])
            pdD = pd.DataFrame(data=testData, index=tempTimeColumnData, columns=["Data"])
            pdR = pd.DataFrame(data=refData, index=tempTimeColumnRef, columns=["Data"])

            cr.Data = pd.DataFrame(data=testData, index=tempTimeColumnData, columns=["Data"])
            cr.RefData = pd.concat([cr.RefData,
                                    pd.DataFrame(data=refData, index=tempTimeColumnData,
                                                 columns=["Data"]).loc[start:end]])

        except ValueError as e:
            printWarning(str(e))
            printWarning(f"        Could not convert given data of file to pandas dataframe.")
            cr.ErrorCode = -15
            return cr

        # We only use data between out start and end point
        pdTime = pd.concat([pdTime, pdT.loc[start:end]])
        pdData = pd.concat([pdData, pdD.loc[start:end]])
        pdRef = pd.concat([pdRef, pdR.loc[start:end]])

        ####### MAXIMUM #######
        try:
            # we evaluate the results
            cr.norms['Maximum'] = sf.function_Maximum(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate Maximum for variable '{variable}'")
        ####### MAXIMUM #######
        try:
            cr.norms['Minimum'] = sf.function_Minimum(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate Minimum for variable '{variable}'")
        ####### MAXIMUM #######
        try:
            cr.norms['Average'] = sf.function_Average(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate Average for variable '{variable}'")
        ####### MAXIMUM #######
        try:
            cr.norms['CVRMSE'] = sf.function_CVRMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate CVRMSE for variable '{variable}'")
        ####### MAXIMUM #######
        try:
            cr.norms['Daily Amplitude CVRMSE'] = sf.function_Daily_Amplitude_CVRMSE(pdRef["Data"], pdData["Data"],
                                                                                    pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate Daily Amplitude CVRMSE for variable '{variable}'")
        ####### MAXIMUM #######
        try:
            cr.norms['MBE'] = sf.function_MBE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate MBE for variable '{variable}'")

        try:
            cr.norms['RMSEIQR'] = sf.function_RMSEIQR(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate RMSIQR for variable '{variable}'")

        try:
            cr.norms['MSE'] = sf.function_MSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate MSE for variable '{variable}'")

        try:
            cr.norms['NMBE'] = sf.function_NMBE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate NMBE for variable '{variable}'")

        try:
            cr.norms['NRMSE'] = sf.function_NRMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate NRMSE for variable '{variable}'")

        try:
            cr.norms['RMSE'] = sf.function_RMSE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate RMSE for variable '{variable}'")

        try:
            cr.norms['RMSLE'] = sf.function_RMSLE(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate RMSLE for variable '{variable}'")

        try:
            cr.norms['R squared'] = sf.function_R_squared_coeff_determination(pdRef["Data"],pdData["Data"],pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate R squared for variable '{variable}'")

        try:
            cr.norms['std dev'] = sf.function_std_dev(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate std dev for variable '{variable}'")

        try:
            cr.norms['Max Difference'] = sf.function_max_difference(pdRef["Data"], pdData["Data"], pdTime["Date and Time"])
        except (RuntimeError, RuntimeWarning) as e:
            printError(f"        {str(e)}")
            printError(f"        Cannot calculate Max Difference for variable '{variable}'")


        # TODO : Wichtung
        if (abs(cr.norms['Average']) < 1e-4):
            cr.score = 0  # prevent division by zero error
        else:
            sum = 999999
            if weightFactors['Sum'] > 0:
                sum = weightFactors['Sum']
            if 'Max Difference' in weightFactors.keys():
                if sum == 999999:
                    sum = 1
                else:
                    sum = sum + 1

            maxDiff = 0
            if "Max Difference" in weightFactors.keys():
                maxDiff = 80.0 + 20.0 * (weightFactors.get('Max Difference', 0) - abs(
                                cr.norms['Max Difference'])) / weightFactors.get('Max Difference', 9999)

            cr.score = cr.score + \
                       (weightFactors.get('CVRMSE', 0) * (100.0 - abs(cr.norms['CVRMSE'])) +  # in %
                        weightFactors.get('Daily Amplitude CVRMSE', 0) * (
                                100.0 - abs(cr.norms['Daily Amplitude CVRMSE'])) +  # in %
                        weightFactors.get('MBE', 0) * (100.0 - 100.0 * abs(cr.norms['MBE']) / cr.norms['Average']) +
                        weightFactors.get('RMSEIQR', 0) * (100.0 - abs(cr.norms['RMSEIQR'])) +  # in %
                        weightFactors.get('MSE', 0) * (100.0 - 100 * abs(cr.norms['MSE']) / cr.norms['Average']) +
                        weightFactors.get('NMBE', 0) * (100.0 - abs(cr.norms['NMBE'])) +  # in %
                        weightFactors.get('NRMSE', 0) * (100.0 - abs(cr.norms['NRMSE'])) +  # in %
                        weightFactors.get('RMSE', 0) * (100.0 - 100.0 * abs(cr.norms['RMSE']) / cr.norms['Average']) +
                        weightFactors.get('RMSLE', 0) * (100.0 - abs(cr.norms['RMSLE']) / cr.norms['Average']) +
                        weightFactors.get('R squared', 0) * (cr.norms['R squared']) +  # in %
                        weightFactors.get('std dev', 0) * (100.0 - abs(cr.norms['std dev']) / cr.norms['Average']) +
                        maxDiff) / sum

    cr.score = cr.score / len(starts)  # normation

    # scoring caluclation --> >95% : Gold | >90% : Silver | >80% : Bronze
    badge = 0
    if (cr.score > 95):
        badge = 1
    elif (cr.score > 90):
        badge = 2
    elif (cr.score > 80):
        badge = 3
    # now set the final SimQuality Badge
    cr.simQbadge = badge
    cr.score = round(cr.score, 2)

    return cr


# all the data is stored in a dictionary with tool-specific data
def processDirectory(path):
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
        printError("    Missing test result directory '{}'.".format(tsvPath))
        return None  # None indicates entirely invalid/missing test data.

    tsvFiles = [o for o in os.listdir(tsvPath) if o.endswith("tsv")]
    evalFiles = [o for o in os.listdir(path) if o.endswith("tsv")]
    if not "Reference.tsv" in evalFiles:
        printError("    Missing 'Reference.tsv' file.")
        return None
    if not "EvaluationPeriods.tsv" in evalFiles:
        printError("    Missing 'EvaluationPeriods.tsv' file.")
        return None
    tsvFiles = sorted(tsvFiles)

    # read evaluation periods
    evalData = TSVContainer()
    evalData.readAsStrings(os.path.join(path, "EvaluationPeriods.tsv"))
    if True in evalData.emptyColumn:
        printError("    'EvaluationPeriods.tsv' contains empty columns.")
        return None

    # read reference file
    refData = TSVContainer()
    refData.readAsStrings(os.path.join(path, "Reference.tsv"))
    if True in refData.emptyColumn:
        printError("    'Reference.tsv' contains empty columns.")
        return None
    if not refData.convert2Double():
        printError("    'Reference.tsv' contains invalid numbers.")
        return None

    # read reference specification
    try:
        with open(os.path.join(path,'References.txt')) as f:
            lines = f.readlines()
            references = lines[0].split(",")
    except RuntimeError as e:
        printError(e)
        printError(f"References.txt needs to be specified. Separated by ','")

    # read Weight factors
    try:
        weightFactorsTSV = TSVContainer()
        weightFactorsTSV.readAsStrings(os.path.join(path, "WeightFactors.tsv"))
    except RuntimeError as e:
        printError(e)
        printError(f"At least one weight factor has to be specified in 'WeightFactors.tsv'.")
        exit(1)

    weightFactors = dict()

    diffFactor = 0
    for i in range(len(weightFactorsTSV.data[0])):
        if weightFactorsTSV.data[0][i] == "Max Difference":
            diffFactor = - float(weightFactorsTSV.data[1][i])
        weightFactors[weightFactorsTSV.data[0][i]] = float(weightFactorsTSV.data[1][i])
    weightFactors['Sum'] = diffFactor + sum(map(float, weightFactorsTSV.data[1]))  # convert to int and then sum it up

    # read Weight factors
    ToolData = []
    try:
        toolData = pd.read_csv(os.path.join(path, "ToolSpecifications.tsv"), encoding='utf-8', sep="\t",
                               engine="pyarrow")
    # toolData = toolData.set_index(['Tool'])
    # toolData = toolData.to_dict('records')
    except RuntimeError as e:
        print(e)
        print(f"Tool Data '{str(ToolData)}' is not specified in directory {path}.")
        exit(1)

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
            printError("    Missing unit in header label '{}' of 'Reference.tsv'".format(v))
            return None
        v = v[0:p].strip()
        variables.append(v)
        printNotification("  {}".format(v))

    # extract variable names
    evaluationVariables = []
    for e in evalData.data[0]:
        evaluationVariables.append(e)
        printNotification("  {}".format(e))

    ###############################################################

    referenceDf = pd.DataFrame()

    tsvData = []
    for dataFile in tsvFiles:

        printNotification("\n-------------------------------------------------------\n")
        printNotification("Generating References.\n")
        printNotification("Reading '{}'.".format(dataFile))
        toolID = dataFile[0:-4]  # strip tsv

        if not toolID in references:
            continue

        tsv = pd.read_csv(os.path.join(tsvPath, dataFile), sep="\t", on_bad_lines='warn')


        referenceDf = referenceDf.add(tsv, fill_value=0)


    ###############################################################

    referenceDf = referenceDf.div(len(references))

    # now read in all the reference files, collect the variable headers and write out the collective file
    tsvData = []
    for dataFile in tsvFiles:
        # special handling of reference data files needed only for visualization
        if dataFile.startswith("Reference"):
            continue

        if dataFile.startswith("EvaluationPeriods"):
            continue

        printNotification("\n-------------------------------------------------------\n")
        printNotification("Reading '{}'.".format(dataFile))
        toolID = dataFile[0:-4]  # strip tsv
        tsv = TSVContainer()
        tsv.readAsStrings(os.path.join(tsvPath, dataFile))
        if True in tsv.emptyColumn:
            printError("    '{}' contains empty columns. Skipped.".format(dataFile))
            appendErrorResults(tsvData, testCaseName, toolID, -10, variables)
            continue

        # if not all data is provieded by a tool we only want to skip the specific variable
        for header in tsv.headers:
            if header not in refData.headers:
                printError(f"    '{dataFile}'s header '{header}' is not part of the reference header. Skipped.")
                continue

        # Check if only valid numbers are in file
        if not tsv.convert2Double():
            printError("    Data file contains invalid numbers. Skipped.")
            appendErrorResults(tsvData, testCaseName, toolID, -7, variables)
            continue

        # process all variables
        for i in range(len(variables)):
            # call function to generate and evaluate all norms for the given variable
            # we provide time column, reference data column and value column, also parameter set for norm calculation
            # we get a variable-specific score stored in CaseResults object
            if not rawVariables[i] in tsv.headers:
                printError("    '{}'s does not contain the variable {}. Skipped".format(dataFile, variables[i]))
                continue

            # check if data even exists
            if i > len(tsv.data):
                printError("    '{}'s columns exceed number of columns of 'Reference.tsv'".format(dataFile))
                appendErrorResults(tsvData, testCaseName, toolID, -11, variables)
                break

            if not variables[i] in evaluationVariables:
                printError(
                    "    'EvaluationPeriods.tsv' does not contain the variable '{}'. Skipped.".format(variables[i]))
                continue

            for j in range(len(evaluationVariables)):
                if variables[i] == evaluationVariables[j]:
                    starts = evalData.data[1][j].split(",")
                    ends = evalData.data[2][j].split(",")
                    break

            if len(starts) != len(ends):
                printError(
                    f"Start and end timpoints for evaluation do not have the same size: {len(start)} vs {len(end)}")

            for j in range(len(starts)):
                start = float(starts[j])
                end = float(ends[j])
                if end < start:
                    printError(
                        "    Evaluation End Point ({}) has to be after start point ({}). Skipped.".format(end, start))
                    continue

                if end > refData.data[0][-1]:
                    printError(
                        "    Evaluation End Point ({}) is bigger then last time stamp of reference results ({}). Skipped.".format(
                            end, refData.data[0][-1]))
                    continue
                if start < refData.data[0][0]:
                    printError(
                        "    Evaluation Start Point ({}) is smaller then first time stamp of reference results ({}). Skipped.".format(
                            end, refData.data[0][0]))
                    continue

            # check if have an hourly time column
            try:
                timeIndicator = tsv.headers[0].split('[')[1].split(']')[0]
            except Exception as e:
                printError(str(e))
                raise Exception(f"Could not convert time unit {tsv.headers[0]} to h.")



            cols = referenceDf.columns
            time = cols[0]
            data = cols[i+1]
            cr = evaluateVariableResults(variables[i], referenceDf[time].tolist(), tsv.data[0], referenceDf[data].tolist(),
                                         tsv.data[i + 1], starts, ends, weightFactors, timeIndicator)
            cr.TestCase = testCaseName
            cr.ToolID = toolID
            cr.Variable = variables[i]
            cr.ErrorCode = 0
            cr.Unit = rawVariables[i].split("[")[1].split("]")[0].strip()

            if toolID in references:
                cr.Reference = True

            try:
                data = toolData.loc[toolData['Tool'] == toolID]
                cr.DisplayName = data['Tool Name'].item()
                cr.Version = data['Tool Version'].item()
                cr.Editor = data['Tool Editor'].item()
                cr.DisplayColor = data['Tool Color'].item()
            except Exception as e:
                printError(str(e))
                raise Exception(f"Data in 'ToolData.tsv' in {path} not specified for Tool '{toolID}'")

            tsvData.append(cr)

    return tsvData

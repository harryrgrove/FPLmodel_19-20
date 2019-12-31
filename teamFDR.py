"""
teamfdr.py creates s Fixture Difficulty ratings (FDRs) for each team based on the statistical quality of their performances in the last two seasons. It is the core of my project, and the most mathematical part of the model. I give each team 4 multipliers from 0 based on their performances at attacking and defending at home and away, and use this to determine mean forcasted goals in a fixture. The most significant problem to be solved is how to accurately map form, which will be discussed.
"""

import json
from understat import Understat
import rawDataUpdate
from collections import OrderedDict
from math import sqrt, e, pi
from copy import deepcopy
from prettytable import PrettyTable
import numpy as np
from random import random


def newDataCheck():  # This function checks that the databases I'm using are correct. Otherwise this part of the algorithm is skipped and the most recently saved FDR is implemented
    import asyncio
    import aiohttp
    from os import path

    if path.exists('results.json'):  # Check if any data files currently exist
        with open('results.json', 'r') as fp:
            savedResults = json.load(fp)  # If so, loads the data for the sake of comparison

        async def main():
            async with aiohttp.ClientSession() as session:  # Opens connection with server
                understat = Understat(session)
                global results
                results = await understat.get_league_results("epl",
                                                             2019)  # Adds the Understat info from every match from the 2018/19 and 2019/20 season to the dataset for comparison

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())  # Closes connection with server
        if results != savedResults:  # Checks for any discrepancies between saved and new datasets
            return True  # If discrepancies exist, update all data = True
    else:
        return True  # If no data files exist, update all data = True


if newDataCheck():
    rawDataUpdate.rawDataUpdate()

with open('teamDB.json', 'r') as fp:
    teamDB = json.load(fp)  # Imports saved team data into script
with open('matchDB.json', 'r') as fp:
    matchDB = json.load(fp)  #  Imports saved match database into script

meanxG, teams = sum([match['hxG'] + match['axG'] for index, match in matchDB.items()]) / len(matchDB) / 2, {i for i in
                                                                                                            teamDB}  # Calculates mean xG

performanceDB = OrderedDict()  # Creates dict which will contain performances of each teams, seperated by offence and defence
for team, matches in teamDB.items():  # Iterates through each team
    performanceDB[team] = {'offence': {'home': OrderedDict(), 'away': OrderedDict()}, 'defence': {'home': OrderedDict(),
                                                                                                  'away': OrderedDict()}}  # Creates dict within database to contain the performances of the team
    for index, matchInfo in matches.items():  # Iterates through team's matches
        performanceDB[team]['offence'][matchInfo['location']][int(index)], \
        performanceDB[team]['defence'][matchInfo['location']][int(index)] = {'perf': matchInfo['xG'] / meanxG,
                                                                             'opponent': matchInfo['opponent']}, {
                                                                                'location': matchInfo['location'],
                                                                                'perf': matchInfo['xC'] / meanxG,
                                                                                'opponent': matchInfo[
                                                                                    'opponent']}  # Adds info from teamDB to performanceDB

"""
A function to "smooth over" (i.e. interpolate) performances to create form ratings. nums = input, sd = standard deviation, dsv = different season value (how much bearing a different season has on current form), prediction = True if function is being used to determine forcasting accuracy, else False.
"""


def smoothNums(nums, sd=8, dsv=1, prediction=False):
    array = []
    for index in range(len(nums)):  # Iterates through each index of the input list
        weights = [
            (1 - (prediction and i >= index)) * (e ** (-(i - index) ** 2 / (2 * sd ** 2)) / sd / sqrt(2 * pi)) * (
                        1 - (1 - dsv) * (1 - (int(i / 19) == int(index / 19)))) for i, num in enumerate(
                nums)]  # This line of code that uses boolean identities to give weights to each number in the input list, incorporating normal dist., dsv and prediction status
        if sum(weights):  # If any weights have been applied (i.e. not 1st step in predictive smoothing process)
            array.append(sum([p * weights[i] for i, p in enumerate(nums)]) / sum(weights))
        else:
            array.append(meanxG)  # If it is the first prediction, predict the mean goals
    return array


"""
The following function, which generates an FDR matrix from the list of performces is the most mathematically significant part of the algorithm. It uses a mathematical iterative congruence process which as far as I am aware is an original idea. You must forgive the ugly nested for loops.
"""


def FDR(DB, offenceSD=5, defenceSD=10, dsv=1,
        complete=False):  # sd and dsv are the optimal stand deviation and different season values calculated by the optimiseVals function.
    DB = deepcopy(DB)
    formDB = {team: {'offence': {'home': {}, 'away': {}}, 'defence': {'home': OrderedDict(), 'away': OrderedDict()}} for
              team in teams}  # Creates data structure similar to performance database, for form ratings
    for team in teams:  # Iterates through each team
        for fence in ('offence', 'defence'):  # Iterates through offence and defence
            for loc in ('home', 'away'):  # Iterates through home and away
                formDB[team][fence][loc] = {}  # Creates dict in which to enter data about every given match
                for matchIndex in DB[team][fence][loc]:
                    formDB[team][fence][loc][matchIndex] = {'form': 1, 'opponent': DB[team][fence][loc][matchIndex][
                        'opponent']}  # Creates dict for each match, containing info about form and opponent

    for repeat in range(
            10):  # Performs iterative process 50 times (totally unneccesary to do it more than 5; gives an answer to a 10^15 degree of accuracy, but it only takes 5 seconds so why not...)
        lastFormDB = deepcopy(
            formDB)  # Remembers previous form data, as the iteration converges towards two oscilating values about 0.01% away, depending on whether offence or defence was calculated first.
        for fence in ['offence', 'defence'][
                     ::int(((repeat % 2 == 1) - 0.5) * 2)]:  # Alternates between iterating through offence and defence
            if fence == 'offence':
                sd = offenceSD
            else:
                sd = defenceSD
            for loc in {'home', 'away'}:  # Iterates through home and away
                for team in teams:  # Iterates through each team
                    perfNums, opponentFormNums = [], []
                    for matchIndex, matchInfo in DB[team][fence][loc].items():
                        perfNums.append(
                            matchInfo['perf'])  # Creates array of given team's performances at given location
                        opponentFormNums.append(formDB[matchInfo['opponent']][
                                                    'offence' * (fence != 'offence') + 'defence' * (
                                                                fence != 'defence')][
                                                    'home' * (loc != 'home') + 'away' * (loc != 'away')][matchIndex][
                                                    'form'])  # Creates array of opponent's forms in respective fixtures
                    newFormNums = smoothNums([num / opponentFormNums[index] for index, num in enumerate(perfNums)], sd,
                                             dsv)  # The new form estimate of the team is a rolling average (but normally distributed) of scaled performances (i.e. depending on strength of opponent)
                    for index, element in enumerate(list(formDB[team][fence][loc].items())):
                        formDB[team][fence][loc][element[0]] = {'form': newFormNums[index], 'opponent': element[1][
                            'opponent']}  # Places these new forms into the form database

    FDRMatrix = {team: {'offence': {'home': {}, 'away': {}}, 'defence': {'home': OrderedDict(), 'away': OrderedDict()}}
                 for team in
                 teams}  # Creates structure for complete FDR Matrix, which averages the oscilating values for a true form value
    for team in teams:  # Iterates through each team
        for fence in ('offence', 'defence'):  # Iterates through offence and defence
            for loc in ('home', 'away'):  # Iterates through home and away
                for matchIndex, matchInfo in formDB[team][fence][loc].items():  # Iterates through info for each match
                    FDRMatrix[team][fence][loc][matchIndex] = {'form': (matchInfo['form'] +
                                                                        lastFormDB[team][fence][loc][matchIndex][
                                                                            'form']) / 2}  # Puts the correct form value in the matrix
    return FDRMatrix


FDR = FDR(performanceDB, 10, 10, 0.8)


def meanFDR(FDRMatrix):  # Calculates the mean fixture difficulty of each team given a season FDR
    FDRMatrix = deepcopy(FDRMatrix)
    for team in FDRMatrix:  # Iterates through each team
        for fence in ('offence', 'defence'):  # Iterates through offence and defence
            for loc in ('home', 'away'):  # Iterates through home and away
                total = 0  # Creates count to derive mean
                for matchIndex, matchInfo in FDRMatrix[team][fence][loc].items():  # For each form value in team FDR
                    total += matchInfo['form']  # Add form to total
                FDRMatrix[team][fence][loc] = total / len(FDRMatrix[team][fence][loc])  # Divide to obtain mean
    return FDRMatrix


meanFDR = meanFDR(FDR)  # Calculate the mean FDR of the season so far
FDRTable = PrettyTable()  # Creates PrettyTable to present the mean FDR over the season
FDRTable.field_names = ["Team", "Offence at Home", "Offence away", "Defence at Home",
                        "Defence Away"]  # Creates table header
for team in sorted(teams,
                   key=lambda i: meanFDR[i]['offence']['home'] / sum([meanFDR[t]['defence']['away'] for t in teams]) +
                                 meanFDR[i]['offence']['away'] / sum([meanFDR[t]['defence']['home'] for t in teams]) -
                                 meanFDR[i]['defence']['home'] / sum([meanFDR[t]['offence']['away'] for t in teams]) -
                                 meanFDR[i]['defence']['away'] / sum([meanFDR[t]['offence']['home'] for t in teams]))[
            ::-1]:  # Sorts teams in first column by overall strength
    FDRTable.add_row([team, str(meanFDR[team]['offence']['home'])[:5], str(meanFDR[team]['offence']['away'])[:5],
                      str(meanFDR[team]['defence']['home'])[:5],
                      str(meanFDR[team]['defence']['away'])[:5]])  # Adds each row of data to the table
print('\n' * 2 + 'Sorted by Mean Overall Strength')
print(FDRTable)

FDRTable = PrettyTable()  # Creates PrettyTable to present the current FDR
FDRTable.field_names = ["Team", "Offence at Home", "Offence away", "Defence at Home",
                        "Defence Away"]  # Creates table header
for team in sorted(teams, key=lambda i: list(FDR[i]['offence']['home'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['defence']['away'].items())[-1][1]['form'] for t in teams]) +
                                        list(FDR[i]['offence']['away'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['defence']['home'].items())[-1][1]['form'] for t in teams]) -
                                        list(FDR[i]['defence']['home'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['offence']['away'].items())[-1][1]['form'] for t in teams]) -
                                        list(FDR[i]['defence']['away'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['offence']['home'].items())[-1][1]['form'] for t in teams]))[
            ::-1]:  # Sorts teams in first column by overall strength
    FDRTable.add_row([team, str(list(FDR[team]['offence']['home'].items())[-1][1]['form'])[:5],
                      str(list(FDR[team]['offence']['away'].items())[-1][1]['form'])[:5],
                      str(list(FDR[team]['defence']['home'].items())[-1][1]['form'])[:5],
                      str(list(FDR[team]['defence']['away'].items())[-1][1]['form'])[
                      :5]])  # Adds each row of data to the table
print('\n' * 2 + 'Sorted by Overall Strength')
print(FDRTable)

FDRTable = PrettyTable()  # Creates PrettyTable to present the current FDR
FDRTable.field_names = ["Team", "Offence at Home", "Offence away"]  # Creates table header
for team in sorted(teams, key=lambda i: list(FDR[i]['offence']['home'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['defence']['away'].items())[-1][1]['form'] for t in teams]) +
                                        list(FDR[i]['offence']['away'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['defence']['home'].items())[-1][1]['form'] for t in teams]))[
            ::-1]:  # Sorts teams in first column by overall strength
    FDRTable.add_row([team, str(list(FDR[team]['offence']['home'].items())[-1][1]['form'])[:5],
                      str(list(FDR[team]['offence']['away'].items())[-1][1]['form'])[
                      :5]])  # Adds each row of data to the table
print('\n' * 2 + 'Sorted by Offensive Strength')
print(FDRTable)

FDRTable = PrettyTable()  # Creates PrettyTable to present the current FDR
FDRTable.field_names = ["Team", "Defence at Home", "Defence Away"]  # Creates table header
for team in sorted(teams, key=lambda i: - list(FDR[i]['defence']['home'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['offence']['away'].items())[-1][1]['form'] for t in teams]) -
                                        list(FDR[i]['defence']['away'].items())[-1][1]['form'] / sum(
        [list(FDR[t]['offence']['home'].items())[-1][1]['form'] for t in teams]))[
            ::-1]:  # Sorts teams in first column by overall strength
    FDRTable.add_row([team, str(list(FDR[team]['defence']['home'].items())[-1][1]['form'])[:5],
                      str(list(FDR[team]['defence']['away'].items())[-1][1]['form'])[
                      :5]])  # Adds each row of data to the table
print('\n' * 2 + 'Sorted by Defensive Strength')
print(FDRTable)

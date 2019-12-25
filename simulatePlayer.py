"""
simulatePlayer.py contains functions to calculate the mean xPts for a player in a given fixture, as well as calculating the mean expected goals and assists for a player in a given fixture. simulateFixtures can connect to the fixture database to calculate each players' xPts in the next n GWs. simulateTeam can caculate the optimal formation and expected points for an entire team.
"""

import simulateMatch
from teamFDR import smoothNums
from getPlayer import getPlayer, playerNames
from collections import OrderedDict
from copy import deepcopy
import json
import numpy as np
from math import e, factorial

with open('playerDB.json', 'r') as fp:
    playerDB = json.load(fp)
with open('matchDB.json', 'r') as fp:
    matchDB = json.load(fp)
with open('fixtureDB.json', 'r') as fp:
    fixtureDB = json.load(fp)

xAConstant = np.mean(
    [(matchInfo['hxA'] / matchInfo['hxG'] + matchInfo['axA'] / matchInfo['axG']) / 2 for matchID, matchInfo in
     matchDB.items()])


def simulateBonus(player, loc, opponent):
    pass


def simulatePts(position, playerName, loc, opponent, SD=5):
    if position == 'DEF' and playerName != 7708:
        SD = 100
    playerName = str(playerName)
    for team, players in playerDB.items():
        for player in players:
            if player == playerName:
                playerTeam, matches = team, OrderedDict(playerDB[team][player])
                break
    for matchID, matchInfo in matches.items():
        if matchInfo['loc'] == 'h':
            matchInfo['teamxG'] = matchDB[matchID]['hxG']
            matchInfo['teamxA'] = matchDB[matchID]['hxA']
        else:
            matchInfo['teamxA'] = matchDB[matchID]['axA']
            matchInfo['teamxG'] = matchDB[matchID]['axG']
    matchesTrue = deepcopy(matches)
    for matchID, matchInfo in matches.items():
        if matchInfo['mins'] < 60:
            del matchesTrue[matchID]
    if len(matchesTrue) > 0:
        xGProportions, xAProportions = [matchInfo['xG'] / matchInfo['teamxG'] for matchID, matchInfo in
                                        matchesTrue.items()], [matchInfo['xA'] / matchInfo['teamxA'] for
                                                               matchID, matchInfo in matchesTrue.items()]
        xGProportion, xAProportion = smoothNums(xGProportions, SD)[-1], smoothNums(xAProportions, SD)[-1]
        if loc == 'home':
            teamxG = simulateMatch.simulateGoals(playerTeam, opponent)[0]
            csProb = simulateMatch.simulateCleanSheet(playerTeam, opponent)[0]
            conceededPts = sum(
                [simulateMatch.resultProb(playerTeam, opponent, j, 2 + i) * int(2 + i / 2) for j in range(12) for i in
                 range(10)])
        else:
            csProb = simulateMatch.simulateCleanSheet(opponent, playerTeam)[1]
            teamxG = simulateMatch.simulateGoals(opponent, playerTeam)[1]
            conceededPts = sum(
                [simulateMatch.resultProb(opponent, playerTeam, 2 + i, j) * int(2 + i / 2) for j in range(12) for i in
                 range(10)])
        teamxA = teamxG * xAConstant

        xPts = 0
        if position == 'DEF' or position == 'GKP':
            xPts = teamxG * xGProportion * 6 + teamxA * xAProportion * 3 + csProb * 4 - conceededPts + 2
        elif position == 'MID':
            xPts = teamxG * xGProportion * 5 + teamxA * xAProportion * 3 + csProb + 2
        else:
            xPts = teamxG * xGProportion * 4 + teamxA * xAProportion * 3 + 2
        return xPts
    return 2.001


def simulateFixtures(playerName, fixtureCount, SD=5):
    playerTeam = 'Norwich'
    if type(playerName) == str:
        playerName = getPlayer(playerName, 'name', 'understat')
    for team, players in playerDB.items():
        for player in players:
            if player == str(playerName):
                playerTeam = team
                break
        else:
            continue
        break

    for player in playerNames:
        if player['understat'] == playerName:
            position = player['position']
            break
    fixtures = list(OrderedDict(fixtureDB[playerTeam]).items())[:fixtureCount]
    points = []
    for matchID, matchInfo in dict(fixtures).items():
        points.append(
            simulatePts(position, playerName, 'home' * (matchInfo['loc'] == 'h') + 'away' * (matchInfo['loc'] == 'a'),
                        matchInfo['opponent'], SD))
    return points


def simulateTeam(playerDict, n=1, SD=5):
    for position, playerList in playerDict.items():
        for i, player in enumerate(playerList):
            if type(player) == str:
                player = getPlayer(player, 'name', 'name')
            playerList[i] = [player, simulateFixtures(position, player, 100, SD)[n - 1]]
    pts = max(playerDict['GKP'], key=lambda x: x[1])
    GKPpts, orderedDEF, orderedMID, orderedFOR = max(playerDict['GKP'], key=lambda x: x[1])[1], sorted(
        playerDict['DEF'], key=lambda x: x[1], reverse=True), sorted(playerDict['MID'], key=lambda x: x[1],
                                                                     reverse=True), sorted(playerDict['FOR'],
                                                                                           key=lambda x: x[1],
                                                                                           reverse=True)
    captain = sorted(orderedDEF + orderedMID + orderedFOR, key=lambda i: i[1], reverse=True)[0]
    DEFlineups, MIDlineups, FORlineups = {3: sum(i[1] for i in orderedDEF[:3]), 4: sum([i[1] for i in orderedDEF[:4]]),
                                          5: sum([i[1] for i in orderedDEF[:5]])}, {
                                             2: sum(i[1] for i in orderedMID[:2]), 3: sum(i[1] for i in orderedMID[:3]),
                                             4: sum([i[1] for i in orderedMID[:4]]),
                                             5: sum([i[1] for i in orderedMID[:5]])}, {
                                             1: sum(i[1] for i in orderedFOR[:1]),
                                             2: sum([i[1] for i in orderedFOR[:2]]),
                                             3: sum([i[1] for i in orderedFOR[:3]])}
    formations = [(a, b, c) for a in range(len(orderedDEF) + 1) for b in range(len(orderedMID) + 1) for c in
                  range(len(orderedFOR) + 1) if a + b + c == 10 and a >= 3 and c >= 1]
    bestForm = []
    for f in formations:
        bestForm.append([DEFlineups[f[0]] + MIDlineups[f[1]] + FORlineups[f[2]],
                         {'GKP': set([max(playerDict['GKP'], key=lambda x: x[1])[0]]),
                          'DEF': set([i[0] for i in orderedDEF[:f[0]]]), 'MID': set([i[0] for i in orderedMID[:f[1]]]),
                          'FOR': set([i[0] for i in orderedFOR[:f[2]]]), 'Bench': sorted(
                             [i[0] for i in orderedDEF[f[0]:]] + [i[0] for i in orderedMID[f[1]:]] + [i[0] for i in
                                                                                                      orderedFOR[
                                                                                                      f[2]:]])}])
    bestForm = max(bestForm, key=lambda x: x[0])
    print(bestForm)
    print(sorted(orderedDEF + orderedMID + orderedFOR, key=lambda i: i[1], reverse=True), '\n')
    return bestForm[0]


def simulateTeamFixtures(playerDict, n=1, SD=5):
    s = 0
    for i in range(n):
        pDict = deepcopy(playerDict)
        print(i + 19)
        s += simulateTeam(pDict, i + 1, SD)
    return s


print('\n' * 2)
SD = 5
gw = 25
player = "Rashford"
print(getPlayer(player, 'name', 'name'), sum(simulateFixtures(player, 100, SD)[0:gw - 18]),
      str(simulateFixtures(player, 100, SD)[0:gw - 18]))
player = 'Y Ings'
print(getPlayer(player, 'name', 'name'), sum(simulateFixtures(player, 100, SD)[0:gw - 18]),
      str(simulateFixtures(player, 100, SD)[0:gw - 18]))
print('\n' * 2)


gw = 19
scores = []
for player in [i for i in playerNames if i['starter'] == True]:
    playerName = player['name']
    playerUnderstat = player['understat']
    scores.append([playerName, simulateFixtures(playerUnderstat, 100, SD)[gw - 19]])
for i in scores:
    if i[1] == None:
        i[1] = 0
for i in sorted(scores, key=lambda i: i[1], reverse=True):
    print(i[0] + ' ' * (30 - len(i[0])) + str(i[1])[:4])
print('\n')
print(
    'Mean among top 20 assets: ' + str(np.mean([i[1] for i in sorted(scores, key=lambda i: i[1], reverse=True)[:30]]))[
                                   :4])

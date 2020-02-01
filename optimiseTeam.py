from pulp import *
import json
from rawDataUpdate import nextGW
from bonus import lineups
from getPlayer import playerNames, getPrice, isStarter, getPlayer, getTeam, getPosition, blacklist
from teamFDR import teams
import binascii

with open('xPtsDB.json', 'r') as fp:
    xPtsDB = json.load(fp)
with open('priceDB.json', 'r') as fp:
    priceDB = json.load(fp)


def compileGWs(start=nextGW, end=38):
    comp = {player: 0 for player in xPtsDB[str(start)]}
    for GW in range(start, end + 1):
        for player, xPts in xPtsDB[str(GW)].items():
            comp[player] += xPts
    return comp


priceDB = {i: priceDB[i] for i in priceDB if int(i) not in blacklist and isStarter(int(i), 'understat') == True}

GWStart, GWEnd = nextGW, nextGW
TV = 100

teamCodes = {team: i for team in teams for i in range(len(teams))}

DB = compileGWs(GWStart, GWEnd)
players = [player for player in DB if int(player) not in blacklist and isStarter(int(player), 'understat') == True]

prob = LpProblem("optimiseTeam", LpMaximize)
useVars = LpVariable.dicts("usePlayer", players, 0, 1, LpBinary)

prob += lpSum([DB[j] * useVars[j] for j in useVars])
prob += lpSum(priceDB[j] * useVars[j] for j in useVars) <= TV - 3.9 * (
            5 - lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'DEF'])) - 4.3 * (
                    5 - lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'MID'])) - 4.3 * (
                    3 - lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'FOR']))
prob += lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'GKP']) == 1
prob += lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'DEF']) >= 3
prob += lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'DEF']) <= 5
prob += lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'MID']) <= 5
prob += lpSum([useVars[i] for i in useVars if getPosition(int(i), 'understat') == 'FOR']) <= 3
for team, lineup in lineups.items():
    prob += lpSum([useVars[i] for i in useVars if int(i) in lineup]) <= 3
prob += lpSum(useVars) == 11

TOL = 0.01
status = prob.solve()
print(LpStatus[status])

print(max(
    [(team, len([x for x in [getTeam(int(i), 'understat') for i in priceDB if useVars[i].varValue > 0.1] if x == team]))
     for team in teams], key=lambda i: i[1])[1])

team = []
for i in priceDB:
    if useVars[i].varValue > 0.1:
        team.append(i)
print('Expected Points: ' + str(sum([DB[i] for i in [j for j in priceDB if useVars[j].varValue > 0.1]]) + max(
    [DB[i] for i in [j for j in priceDB if useVars[j].varValue > 0.1]])))
print(
    'Formation: ' + str(len([player for player in team if getPosition(int(player), 'understat') == 'DEF'])) + '-' + str(
        len([player for player in team if getPosition(int(player), 'understat') == 'MID'])) + '-' + str(
        len([player for player in team if getPosition(int(player), 'understat') == 'FOR'])))
for player in sorted([player for player in team if getPosition(int(player), 'understat') == 'GKP'], key=lambda i: DB[i],
                     reverse=True):
    print('GKP ' + getPlayer(int(player), 'understat', 'name'), round(DB[player], 2))
for player in sorted([player for player in team if getPosition(int(player), 'understat') == 'DEF'], key=lambda i: DB[i],
                     reverse=True):
    print('DEF ' + getPlayer(int(player), 'understat', 'name'), round(DB[player], 2))
for player in sorted([player for player in team if getPosition(int(player), 'understat') == 'MID'], key=lambda i: DB[i],
                     reverse=True):
    print('MID ' + getPlayer(int(player), 'understat', 'name'), round(DB[player], 2))
for player in sorted([player for player in team if getPosition(int(player), 'understat') == 'FOR'], key=lambda i: DB[i],
                     reverse=True):
    print('FOR ' + getPlayer(int(player), 'understat', 'name'), round(DB[player], 2))

for player in team:
    TV -= priceDB[player]
print(round(TV, 1))

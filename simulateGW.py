"""SimulateGW.py calculates expected points for each player expected to start in a given GW, with bonus points added"""

from simulatePlayer import simulatePts, simulateFixtures, simulateTeam, simulateTeamFixtures, fixtureDB
from getPlayer import getPlayer, playerNames, getPosition
from bonus import simulateBonus, lineups
import numpy as np

GW = 22
SD = 10
fixtures = [[team, list(i.items())[GW - 21][1]['opponent']] for team, i in fixtureDB.items() if
            list(i.items())[21 - GW][1]['loc'] == 'h']

playerDict = {}
for team, lineup in lineups.items():
    for player in lineup:
        playerDict[player] = 0

for fixture in fixtures:
    for player, pts in simulateBonus(fixture[0], fixture[1], SD).items():
        playerDict[player] += pts
print(sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True))

print('\n')
for player in playerDict:
    playerDict[player] += simulateFixtures(player, 30, SD)[GW - 21]
for i in sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True):
    print(getPlayer(i[0], 'understat', 'name') + '.' * (30 - len(getPlayer(i[0], 'understat', 'name'))) + str(i[1])[
                                                                                                          :4] + (
                      4 - len(str(i[1]))) * '0')

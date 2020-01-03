"""SimulateGW.py calculates expected points for each player expected to start in a given GW, with bonus points added"""

from simulatePlayer import simulatePts, simulateFixtures, simulateTeam, simulateTeamFixtures, fixtureDB
from getPlayer import getPlayer, playerNames, getPosition
from bonus import simulateBonus, lineups
import numpy as np

print('\n' * 2)

gw = 27
SD = 10

np.mode(1, 1, 1)
fixtureDict = {i: [] for i in range(22, 39)}
for GW in range(22, 39):
    for team in fixtureDB:
        if fixtureDB[team][list(fixtureDB[team])[GW - 22]]['loc'] == 'h':
            fixtureDict[GW].append([team, fixtureDB[team][list(fixtureDB[team])[GW - 22]]['opponent']])
fixtureDict[24].append(['West Ham', 'Liverpool'])
fixtures = fixtureDict[gw]
playerDict = {}
for team, lineup in lineups.items():
    for player in lineup:
        playerDict[player] = 0

for fixture in fixtures:
    print(fixture[0] + '.' * (44 - len(fixture[0] + fixture[1])) + fixture[1])

for fixture in fixtures:
    for player, pts in simulateBonus(fixture[0], fixture[1], SD).items():
        playerDict[player] += pts
print('\n' * 2)
print('Most bonus points:', [(getPlayer(i[0], 'understat', 'name'), i[1]) for i in
                             sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True)[:10]])

for fixture in fixtures:
    for player, pts in simulateBonus(fixture[0], fixture[1], SD).items():
        if player in lineups[fixture[0]]:
            loc = 'h'
        elif player in lineups[fixture[1]]:
            loc = 'a'
        playerDict[player] += simulatePts(getPosition(player, 'understat'), player, loc,
                                          (loc == 'h') * fixture[1] + (loc == 'a') * fixture[0], SD)

print('\n')

for i in sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True):
    print(getPlayer(i[0], 'understat', 'name') + '.' * (30 - len(getPlayer(i[0], 'understat', 'name'))) + str(i[1])[
                                                                                                          :4] + (
                      4 - len(str(i[1]))) * '0')

print('Mean among top 21 assets: ' + str(
    np.mean([i[1] for i in sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True)[:30]]))[:4])

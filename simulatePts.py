from rawDataUpdate import nextGW
from getPlayer import getPlayer, getPosition
from bonus import lineups
import json

with open('xPtsDB.json', 'r') as fp:
    xPtsDB = json.load(fp)


def simulatePtsRun(name, GWEnd, GWStart=nextGW):
    points = []
    for GW in range(GWStart, GWEnd + 1):
        points.append(xPtsDB[str(GW)][str(name)])
    return points


def GWForecast(GW=nextGW):
    return sorted([(int(i[0]), i[1]) for i in list(xPtsDB[str(GW)].items())], key=lambda i: i[1], reverse=True)


if __name__ == '__main__':
    playerDict = {}
    for team, lineup in lineups.items():
        for player in lineup:
            playerDict[player] = sum(simulatePtsRun(player, 27))
    for player in sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True):
        print(getPlayer(player[0], 'understat', 'name') + '.' * (
                    30 - len(getPlayer(player[0], 'understat', 'name'))) + str(round(player[1], 1)))
    print('\n')
    end = 30
    player = 'Martial'
    print(sum(simulatePtsRun(getPlayer(player), end, nextGW)), simulatePtsRun(getPlayer(player), end, nextGW))
    player = 'Grealish'
    print(sum(simulatePtsRun(getPlayer(player), end, nextGW)), simulatePtsRun(getPlayer(player), end, nextGW))
    print('\n')
    for player in GWForecast(nextGW):
        if getPosition(player[0], 'understat') == 'MID':
            print(getPlayer(player[0], 'understat', 'name') + '.' * (
                        30 - len(getPlayer(player[0], 'understat', 'name'))) + str(round(player[1], 2)) + '0' * (
                              4 - len(str(round(player[1], 2)))))

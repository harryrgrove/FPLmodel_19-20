from getPlayer import getPlayer
from bonus import lineups
import json

with open('xPtsDB.json', 'r') as fp:
    xPtsDB = json.load(fp)


def simulatePtsRun(name, GWEnd, GWStart=22):
    points = []
    for GW in range(GWStart, GWEnd + 1):
        points.append(xPtsDB[str(GW)][str(name)])
    return points


def GWForecast(GW=22):
    return sorted([(int(i[0]), i[1]) for i in list(xPtsDB[str(GW)].items())], key=lambda i: i[1], reverse=True)


if __name__ == '__main__':
    playerDict = {}
    for team, lineup in lineups.items():
        for player in lineup:
            playerDict[player] = sum(simulatePtsRun(player, 38))
    for player in sorted(list(playerDict.items()), key=lambda i: i[1], reverse=True):
        print(getPlayer(player[0], 'understat', 'name') + '.' * (
                    30 - len(getPlayer(player[0], 'understat', 'name'))) + str(round(player[1], 1)))
    print('\n')
    end = 27
    player = 'Salah'
    print(sum(simulatePtsRun(getPlayer(player), end)), simulatePtsRun(getPlayer(player), end))
    player = 'Danny Ings'
    print(sum(simulatePtsRun(getPlayer(player), end)), simulatePtsRun(getPlayer(player), end))
    print('\n')
    for player in GWForecast(22):
        print(getPlayer(player[0], 'understat', 'name') + '.' * (
                    30 - len(getPlayer(player[0], 'understat', 'name'))) + str(round(player[1], 2)) + '0' * (
                          4 - len(str(round(player[1], 2)))))

from teamFDR import teams
from simulateMatch import simulateCleanSheet, poisson
from simulatePlayer import simulateReturns, xAConstant
from getPlayer import getPlayer, playerNames, getPosition
from random import random
import numpy as np

lineups = {team: [] for team in teams}
for team in teams:
    for playerInfo in [i for i in playerNames if i['team'] == team and i['starter'] == True]:
        lineups[team].append(playerInfo['understat'])


def simulateBonus(homeTeam, awayTeam, SD):
    homeLineup, awayLineup = lineups[homeTeam], lineups[awayTeam]
    xReturns = {player: [] for player in homeLineup + awayLineup}
    bonus = {player: [] for player in homeLineup + awayLineup}
    for player in homeLineup:
        xReturns[player] = simulateReturns(getPosition(player, 'understat'), player, 'h', awayTeam, SD) + [
            getPosition(player, 'understat')]
    for player in awayLineup:
        xReturns[player] = simulateReturns(getPosition(player, 'understat'), player, 'a', homeTeam, SD) + [
            getPosition(player, 'understat')]
    CSOdds = simulateCleanSheet(homeTeam, awayTeam)
    trials = 10000
    for repeat in range(trials):
        homeBPS, awayBPS = {player: 0 for player in homeLineup}, {player: 0 for player in awayLineup}
        for player in homeLineup:
            goals = np.random.poisson(xReturns[player][0])
            for goal in range(goals):
                homeBPS[player] += {'GKP': 12, 'DEF': 12, 'MID': 18, 'FOR': 24}[xReturns[player][2]]
                if random() < xAConstant:
                    assist = [[player, xReturns[player][1]] for player in [i for i in homeLineup if i != player]]
                    r = random() * sum([i[1] for i in assist])
                    for entry in assist:
                        if r < entry[1]:
                            homeBPS[entry[0]] += 9
                            break
                        r -= entry[1]
        if random() < CSOdds[0]:
            for player in [player for player in homeLineup if
                           xReturns[player][2] == 'GKP' or xReturns[player][2] == 'DEF']:
                homeBPS[player] += 12

        for player in awayLineup:
            goals = np.random.poisson(xReturns[player][0])
            for goal in range(goals):
                awayBPS[player] += {'GKP': 12, 'DEF': 12, 'MID': 18, 'FOR': 24}[xReturns[player][2]]
                if random() < xAConstant:
                    assist = [[player, xReturns[player][1]] for player in [i for i in awayLineup if i != player]]
                    r = random() * sum([i[1] for i in assist])
                    for entry in assist:
                        if r < entry[1]:
                            awayBPS[entry[0]] += 9
                            break
                        r -= entry[1]
        if random() < CSOdds[1]:
            for player in [player for player in awayLineup if
                           xReturns[player][2] == 'GKP' or xReturns[player][2] == 'DEF']:
                awayBPS[player] += 12

        BPS = sorted([(i[0], i[1] + random() - 0.5) for i in list({**homeBPS, **awayBPS}.items())], key=lambda x: x[1],
                     reverse=True)
        bonus[BPS[0][0]].append(3)
        bonus[BPS[1][0]].append(2)
        bonus[BPS[2][0]].append(1)
    for player, scores in bonus.items():
        bonus[player] = sum(scores) / trials
    return bonus


if __name__ == '__main__':
    print('\n' * 2)
    print(sorted(list(simulateBonus('Liverpool', 'Norwich', 10).items()), key=lambda x: x[1], reverse=True))

import teamFDR
from prettytable import PrettyTable
from math import e, factorial
from random import random


def poisson(l, x):
    return l ** x * e ** -l / factorial(x)


def resultProb(homeTeam, awayTeam, homeResult, awayResult, homeScored=0, awayScored=0, minutes=0):
    lHome, lAway = homeScored + list(teamFDR.FDR[homeTeam]['offence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['defence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                               1 - (minutes / 90)), awayScored + \
                   list(teamFDR.FDR[homeTeam]['defence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['offence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                               1 - (minutes / 90))
    return poisson(lHome, homeResult) * poisson(lAway, awayResult)


def simulate(homeTeam, awayTeam, homeScored=0, awayScored=0, minutes=0):
    lHome, lAway = homeScored + list(teamFDR.FDR[homeTeam]['offence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['defence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                               1 - (minutes / 90)), awayScored + \
                   list(teamFDR.FDR[homeTeam]['defence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['offence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                               1 - (minutes / 90))

    homeProb, awayProb = 0, 0
    for homeGoals in range(100):
        for awayGoals in range(100):
            if homeGoals > awayGoals:
                homeProb += resultProb(homeTeam, awayTeam, homeGoals, awayGoals, homeScored, awayScored, minutes)
            elif homeGoals < awayGoals:
                awayProb += resultProb(homeTeam, awayTeam, homeGoals, awayGoals, homeScored, awayScored, minutes)

    print('Expected Goals at 90 mins:')
    expectedGoalsMatrix = PrettyTable()
    expectedGoalsMatrix.field_names = [homeTeam, awayTeam]
    expectedGoalsMatrix.add_row([str(lHome)[:4], str(lAway)[:4]])
    print(expectedGoalsMatrix, '\n' * 2)

    print('Probability of each result at 90 mins:')
    resultProbMatrix = PrettyTable()
    resultProbMatrix.field_names = [homeTeam + ' win: ', 'Draw: ', awayTeam + ' win: ']
    resultProbMatrix.add_row([str(homeProb * 100)[:str(homeProb * 100).find('.') + 3] + '%',
                              str((1 - homeProb - awayProb) * 100)[
                              :str((1 - homeProb - awayProb) * 100).find('.') + 3] + '%',
                              str(awayProb * 100)[:str(awayProb * 100).find('.') + 3] + '%'])
    print(resultProbMatrix, '\n' * 2)

    print('Most likely result at 90 mins:')
    likelyResultMatrix = PrettyTable()
    likelyResultMatrix.field_names = [homeTeam, awayTeam]
    likelyResultMatrix.add_row([int(lHome), int(lAway)])
    print(likelyResultMatrix, '\n' * 2)

    print('Clean Sheet Probability')
    cleanSheetMatrix = PrettyTable()
    cleanSheetMatrix.field_names = [homeTeam, awayTeam]
    cleanSheetMatrix.add_row([str(e ** -lAway * 100)[:4] + '%', str(e ** -lHome * 100)[:4] + '%'])
    print(cleanSheetMatrix, '\n' * 2)


def simulateCleanSheet(homeTeam, awayTeam, homeScored=0, awayScored=0, minutes=0):
    lHome, lAway = homeScored + list(teamFDR.FDR[homeTeam]['offence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['defence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                               1 - (minutes / 90)), awayScored + \
                   list(teamFDR.FDR[homeTeam]['defence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['offence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                               1 - (minutes / 90))
    return (e ** -lAway, e ** -lHome)


def simulateGoals(homeTeam, awayTeam, homeScored=0, awayScored=0, minutes=0):
    return (homeScored + list(teamFDR.FDR[homeTeam]['offence']['home'].items())[-1][1]['form'] *
            list(teamFDR.FDR[awayTeam]['defence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                        1 - (minutes / 90)),
            awayScored + list(teamFDR.FDR[homeTeam]['defence']['home'].items())[-1][1]['form'] *
            list(teamFDR.FDR[awayTeam]['offence']['away'].items())[-1][1]['form'] * teamFDR.meanxG * (
                        1 - (minutes / 90)))


def randResult(homeTeam, awayTeam):
    lHome, lAway = list(teamFDR.FDR[homeTeam]['offence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['defence']['away'].items())[-1][1]['form'] * teamFDR.meanxG, \
                   list(teamFDR.FDR[homeTeam]['defence']['home'].items())[-1][1]['form'] * \
                   list(teamFDR.FDR[awayTeam]['offence']['away'].items())[-1][1]['form'] * teamFDR.meanxG
    hRand, aRand, hGoals, aGoals, hProb, aProb, homeFinished, awayFinished = random(), random(), 0, 0, 0, 0, False, False
    while homeFinished == False or awayFinished == False:
        hProb += poisson(lHome, hGoals)
        aProb += poisson(lAway, aGoals)
        if hRand < hProb and homeFinished == False:
            homeFinished = True
        elif homeFinished == False:
            hGoals += 1
        if aRand < aProb and awayFinished == False:
            awayFinished = True
        elif awayFinished == False:
            aGoals += 1
    return (hGoals, aGoals)


if __name__ == '__main__':
    print('\n' * 2)
    simulate('Sheffield United', 'Watford', 0, 0, 0)

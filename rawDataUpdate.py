"""
rawData.py contiains functions for messy data formatting, which I want to keep seperate from my model.
It collects data from Understat to produce a team performance database which is used in my fixture difficulty ratings, and further to analyse recent xG and xA form of players compared to the teams around them.
It also collects data from u/vaastav's FPL database which is used in my model to forecast Bonus Points.
"""

nextGW = 25


def rawDataUpdate():
    import asyncio
    import aiohttp
    import json
    from time import time
    from understat import Understat
    from fpl import FPL
    from collections import OrderedDict
    from getPlayer import getPlayer, getPosition, playerNames, isStarter, blacklist
    import numpy as np
    import csv
    import requests

    """
    The following loop writes 4 seperate json dicts:
    matchDB is a database of the teams that play and the score in each fixture.
    {'matchID': {'homeTeam': homeTeam, 'awayTeam': awayTeam, 'homeScore': homeScore, 'awayScore': awayScore}}
    playerDB is a database of players' performances in every fixture that they have played since the start of the 2018/19 season.
    playerDB = {'team': {'player': {'matchID': {'mins': mins, xG': xG, 'xA': xA}}}}
    teamDB is a database of teams' performances in every match.
    teamDB = {'team': {'matchID': {'location': home/away, 'opponent': opponent, 'xG': xG, 'xC': xC}}}
    fixtureDB is a database of each team's fixtures until the end of the season.
    fixtureDB = {team: {'location': location, 'opponent': opponent, gw': gw}}

    """

    def getPrice(title, inp='fpl'):
        if inp == 'understat' or inp == 'name':
            title = getPlayer(title, inp, 'fpl')

        async def main():
            async with aiohttp.ClientSession() as session:
                fpl = FPL(session)
                await fpl.login(email='jameshpalmer2000', password='1')
                player = await fpl.get_player(title, return_json=True)
                global price
                price = (player['now_cost'] / 10)

        loop = asyncio.get_event_loop()
        loop.run_until_complete(main())  # Closes connection with server
        return price

    with open('xPtsDB.json', 'r') as fp:
        xPtsDB = json.load(fp)
    priceDB = {}
    for player in [i['understat'] for i in playerNames if i['understat']]:
        print('\n' * 20)
        print(getPlayer(int(player), 'understat', 'name') + ' price appended')
        priceDB[player] = getPrice(int(player), 'understat')
    with open('priceDB.json', 'w') as fp:
        json.dump(priceDB, fp)

    async def main():
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)  # Opens connection with Understat server
            results = await understat.get_league_results("epl",
                                                         2019)  # Adds the Understat info from every match from the 2018/19 and 2019/20 season to the dataset
            teams = set()
            for matchInfo in results:
                teams.update([matchInfo['h']['title'],
                              matchInfo['a']['title']])  # Iterates through matches to add teams to teams set

            squads = {team: [] for team in teams}

            def baselineBonus(understat):
                poisition = getPosition(understat, 'understat')
                mean, sd = 0, 0
                GWStats, baselineBPS = [], []
                name = getPlayer(understat, 'understat', 'name').replace(' ', '_', 1)
                exceptions = {619: 'Sergio_Ag%C3%BCero', 3293: 'Lucas_Rodrigues Moura da Silva',
                              1040: 'José Ángel_Esmorís Tasende', 1208: 'Felipe Anderson_Pereira Gomes',
                              5741: 'Jorge Luiz_Frello Filho', 1663: 'Johann Berg_Gudmundsson',
                              1676: 'David_Luiz Moreira Marinho', 1724: 'Isaac_Success Ajayi',
                              2132: 'José Ignacio_Peleteiro Romallo', 2379: 'João Pedro Cavaco_Cancelo',
                              2383: 'André Filipe_Tavares Gomes', 2446: 'Daniel_Ceballos Fernández',
                              3303: 'Ricardo Domingos_Barbosa Pereira', 3422: 'João Filipe Iria_Santos Moutinho',
                              5245: 'Bernardo_Fernandes da Silva Junior',
                              3635: 'Bernardo Mota_Veiga de Carvalho e Silva', 5543: 'Gabriel Fernando_de Jesus',
                              5675: 'Ismaïla_Sarr', 579: 'Nathan_Aké', 6122: 'Douglas Luiz_Soares de Paulo',
                              614: 'Fernando_Luiz Rosa', 6817: 'Frederico_Rodrigues de Paula Santos',
                              6853: 'Rúben Diogo_da Silva Neves', 6856: 'Rúben Gonçalo_Silva Nascimento Vinagre',
                              700: 'Willian_Borges Da Silva', 7752: 'Gabriel Teodoro_Martinelli Silva',
                              87: 'Joelinton Cássio_Apolinário de Lira'}
                if understat in exceptions:
                    name = exceptions[understat]
                url = 'https://raw.githubusercontent.com/vaastav/Fantasy-Premier-League/master/data/2019-20/players/' + name + '_' + str(
                    getPlayer(understat, 'understat', 'fpl')) + '/gw.csv'
                r = requests.get(url)
                text = r.iter_lines()
                reader = csv.reader(text, delimiter=',')
                for line in text:
                    if str(line) == "b'404: Not Found'":
                        if understat in exceptions:
                            print(understat)
                        return (0, 0)
                    GWStats.append(str(line)[2:-1].split(","))
                for row in GWStats[1:]:
                    if row != ['']:
                        if int(row[12]) >= 60:
                            baselineBPS.append(int(row[2]) - int(row[8]) * (
                                        12 * (poisition == 'DEF' or poisition == 'GKP') + 18 * (
                                            poisition == 'MID') + 24 * (poisition == 'FOR')) - int(row[0]) * 9 - int(
                                row[3]) * 12 * (poisition == 'DEF' or poisition == 'MID'))
                if len(baselineBPS) < 1:
                    return (0, 0)
                return (np.mean(baselineBPS), np.std(baselineBPS))

            for team in teams:
                for playerInfo in [i for i in playerNames if i['team'] == team]:
                    squads[team].append(playerInfo['understat'])
            baselineDB = {team: {} for team in teams}
            count = 0
            for team, squad in squads.items():
                count += 1
                print('\n' * 20)
                print(str(count) + '/20: ' + team + ' bonus point data collecting...')
                for player in squad:
                    if player:
                        baselineDB[team][int(player)] = baselineBonus(player)
            print(baselineDB)

            with open('baselineDB.json', 'w') as fp:
                json.dump(baselineDB, fp)

            matchDB, playerDB, teamDB = OrderedDict(), {team: {} for team in teams}, {team: {} for team in
                                                                                      teams}  # Sets up starting conditions for the creation of database dicts

            totalProgress, countProgress, startTime = len(
                results), 0, time()  # Initialises timing variables to give time estimate

            for matchInfo in results:
                homeTeam, awayTeam, matchID = matchInfo['h']['title'], matchInfo['a']['title'], int(
                    matchInfo['id'])  # Assigns variables for the home team, away team and ID of each fixture
                matchDB[matchID] = {'homeTeam': homeTeam, 'awayTeam': awayTeam, 'hxG': float(matchInfo['xG']['h']),
                                    'axG': float(matchInfo['xG']['a']), 'hxA': 0, 'axA': 0,
                                    'homeScore': int(matchInfo['goals']['h']),
                                    'awayScore': int(matchInfo['goals']['a']),
                                    'date': matchInfo['datetime'][0:10]}  # Adds fixture data to the matchDB dict

                if homeTeam not in teamDB:
                    teamDB[homeTeam] = {}
                if awayTeam not in teamDB:
                    teamDB[awayTeam] = {}  # Adds a team to teamDB if not already added
                teamDB[homeTeam][matchID] = {'location': 'home', 'opponent': awayTeam,
                                             'xG': float(matchInfo['xG']['h']), 'xC': float(matchInfo['xG']['a'])}
                teamDB[awayTeam][matchID] = {'location': 'away', 'opponent': homeTeam,
                                             'xG': float(matchInfo['xG']['a']), 'xC': float(matchInfo['xG'][
                                                                                                'h'])}  # Adds team data of the fixture to teamDB. This is used in formulating the Strength Value Matrix in teamFDR.py.

                countProgress += 1
                timeProgress = time() - startTime
                print('\n' * 20 + 'Estimated Time Remaining: ' + str(
                    (timeProgress / countProgress) * (totalProgress - countProgress))[0:str(
                    (timeProgress / countProgress) * (totalProgress - countProgress)).find(
                    '.')] + ' seconds')  # Provides elementary estimate for time remaining in data update

                for match in [
                    await understat.get_match_players(matchID)]:  # Iterates through all PL matches in the dataset
                    for team, playerDict in match.items():  # Iterates through both teams in the given match
                        if team == 'h':  # For home team
                            for playerID, playerAttributes in playerDict.items():  # Iterates through every player in the given team
                                matchDB[matchID]['hxA'] += float(playerAttributes['xA'])
                                if playerAttributes['player_id'] not in playerDB[homeTeam]:
                                    playerDB[homeTeam][playerAttributes['player_id']] = {}
                                playerDB[homeTeam][playerAttributes['player_id']][matchID] = {
                                    'mins': int(playerAttributes['time']), 'xG': float(playerAttributes['xG']),
                                    'xA': float(playerAttributes['xA']), 'position': playerAttributes['position'],
                                    'yellows': playerAttributes['yellow_card'],
                                    'loc': 'h'}  # Adds player to playerDB if not already contained
                        elif team == 'a':  # Same as above if statement for away team
                            for playerID, playerAttributes in playerDict.items():
                                matchDB[matchID]['axA'] += float(playerAttributes['xA'])
                                if playerAttributes['player_id'] not in playerDB[awayTeam]:
                                    playerDB[awayTeam][playerAttributes['player_id']] = {}
                                playerDB[awayTeam][playerAttributes['player_id']][matchID] = {
                                    'mins': int(playerAttributes['time']), 'xG': float(playerAttributes['xG']),
                                    'xA': float(playerAttributes['xA']), 'position': playerAttributes['position'],
                                    'yellows': playerAttributes['yellow_card'], 'loc': 'a'}
            print('\n' * 20 + 'Data Collection Complete')

            with open('matchDB.json', 'w') as fp:
                json.dump(matchDB, fp)
            with open('playerDB.json', 'w') as fp:
                json.dump(playerDB, fp)
            with open('teamDB.json', 'w') as fp:
                json.dump(teamDB, fp)  # Compiles each dict as a JSON file to be used in teamFDR.py
            with open('results.json', 'w') as fp:
                json.dump(results, fp)  # Saves initial data to check for updates on teamFDR.py

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())  # Closes connection with server

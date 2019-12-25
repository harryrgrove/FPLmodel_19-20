"""
rawData.py contiains functions for messy data formatting, which I want to keep seperate from my model.
It collects data from Understat to produce a team performance database which is used in my fixture difficulty ratings, and further to analyse recent xG and xA form of players compared to the teams around them.
It also collects data from u/vaastav's FPL database which is used in my model to forecast Bonus Points.
"""


def rawDataUpdate():
    import asyncio
    import aiohttp
    import json
    from time import time
    from understat import Understat
    from collections import OrderedDict

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

    async def main():
        async with aiohttp.ClientSession() as session:
            understat = Understat(session)  # Opens connection with Understat server
            results = await understat.get_league_results("epl",
                                                         2019)  # Adds the Understat info from every match from the 2018/19 and 2019/20 season to the dataset
            teams = set()
            for matchInfo in results:
                teams.update([matchInfo['h']['title'],
                              matchInfo['a']['title']])  # Iterates through matches to add teams to teams set

            matchDB, playerDB, teamDB, fixtureDB = OrderedDict(), {team: {} for team in teams}, {team: {} for team in
                                                                                                 teams}, {
                                                   team: OrderedDict() for team in
                                                   teams}  # Sets up starting conditions for the creation of database dicts

            for i, team in enumerate(teams):
                fixtures = await understat.get_team_fixtures(team, 2019)
                for fixture in fixtures:
                    print(fixture)
                    fixtureDB[team][int(fixture['id'])] = {'loc': fixture['side'], 'opponent':
                        fixture['a' * (fixture['side'] == 'h') + 'h' * (fixture['side'] == 'a')]['title']}
                print('\n' * 20 + str(i + 1) + '/20 fixtures updated')

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
            with open('fixtureDB.json', 'w') as fp:
                json.dump(fixtureDB, fp)
            with open('teamDB.json', 'w') as fp:
                json.dump(teamDB, fp)  # Compiles each dict as a JSON file to be used in teamFDR.py
            with open('results.json', 'w') as fp:
                json.dump(results, fp)  # Saves initial data to check for updates on teamFDR.py

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())  # Closes connection with server

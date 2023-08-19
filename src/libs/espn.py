from datetime import datetime
from PIL import Image, ImageDraw, ImageFont
import requests
import matplotlib.pyplot as plt

from ..libs.database import get_database

GET_PLAYERS_ENDPOINT = "https://fantasy.espn.com/apis/v3/games/ffl/seasons/{}/players?scoringPeriodId=0&view=players_wl"
GET_LEAGUE_ENDPOINT = 'https://fantasy.espn.com/apis/v3/games/ffl/seasons/{0}/segments/0/leagues/{1}'

LEAGUE_ID = get_database("espn_league_id")
COOKIES = get_database("espn_cookies")
OWNER_MAPPING = get_database("espn_owner_mapping")


def get_current_matchups(year=None, week_id=None):
    year = year or datetime.today().year
    resp = requests.get(GET_LEAGUE_ENDPOINT.format(year, LEAGUE_ID), cookies=COOKIES)
    data = resp.json()
    teams = data['teams']
    team_mapping = {}
    for team in teams:
        team_mapping[team['id']] = f"{team['location'].strip()} {team['nickname'].strip()}"

    resp = requests.get(GET_LEAGUE_ENDPOINT.format(year, LEAGUE_ID), params={'view': "mMatchup"}, cookies=COOKIES)
    data = resp.json()
    matchups = []
    week_id = week_id or data['scoringPeriodId']
    for matchup in data['schedule']:
        if matchup['matchupPeriodId'] != week_id:
            continue
        else:
            matchups.append((team_mapping[matchup['home']['teamId']], team_mapping[matchup['away']['teamId']]))
    return matchups

def generate_matchups_image(year=None, week_id=None):
    matchups = get_current_matchups(year, week_id)
    if not matchups:
        return None
    template_main = Image.open("res/fantasy_matchup_template.png")
    template = template_main.copy()
    editor = ImageDraw.Draw(template)
    font = ImageFont.truetype("res/ADLaMDisplay-Regular.ttf", 24)
    text_color = (255, 255, 255)

    starting_point = (50, 375)
    offset = 0
    for (home, away) in matchups:
        x, y = starting_point
        y += offset
        offset += 58
        editor.text((x, y), home, fill=text_color, font=font)
        editor.text((x + 850, y), away, fill=text_color, font=font)
    filename = 'matchups.png'
    template.save(filename)
    return filename


def total_wins_over(starting_year=None):
    current_year = datetime.today().year
    starting_year = starting_year or current_year
    total_wins = {}
    for year in range(starting_year, current_year + 1):
        team_resp = requests.get(GET_LEAGUE_ENDPOINT.format(year, LEAGUE_ID), cookies=COOKIES)
        team_data = team_resp.json()
        teams = team_data['teams']
        members = team_data['members']

        team_mapping = {}
        for team in teams:
            for member in members:
                if member['id'] in team['owners']:
                    owner = OWNER_MAPPING.get(member['id'])
                    team_mapping[team['id']] = owner
                    if owner not in total_wins:
                        total_wins[owner] = 0
                    break
            else:
                continue

        history_resp = requests.get(
            GET_LEAGUE_ENDPOINT.format(year, LEAGUE_ID), params={'view': "mMatchup"}, cookies=COOKIES)
        history_data = history_resp.json()

        for matchup in history_data['schedule']:
            winner = matchup['winner']
            if winner == "UNDECIDED":
                continue
            winning_id = matchup[winner.lower()]['teamId']
            winning_owner = team_mapping[winning_id]
            prev_wins = total_wins[winning_owner]
            total_wins[winning_owner] = prev_wins + 1
    return {k: v for k, v in sorted(total_wins.items(), key=lambda item: item[1])}


def generate_wins_bar_graph(starting_year=None):
    data = total_wins_over(starting_year)
    names = list(data.keys())
    values = list(data.values())
    plt.bar(range(len(data)), values, tick_label=names)
    for i in range(len(names)):
        plt.text(i,values[i],values[i])
    plt.xticks(rotation=25)
    filename = 'wins_bar.png'
    plt.savefig(filename)
    return filename

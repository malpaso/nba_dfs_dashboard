"""
Contains functions that map to api_request routes.

- /lineups
"""

from flask import request
import json
import pandas as pd
import numpy as np
import requests
from bs4 import BeautifulSoup
from .. import app
from .. import db_utils
from .utils import match_name, map_team_abbrevs, get_player_ids, get_team_abbrev_team_id_map


ROTOWIRE_URL = 'https://www.rotowire.com/basketball/nba_lineups.htm'
NBA_LINEUP_URL = 'http://stats.nba.com/stats/teamplayerdashboard?DateFrom=&DateTo=&GameSegment=&LastNGames=0&LeagueID=00&Location=&MeasureType=Base&Month=0&OpponentTeamID=0&Outcome=&PORound=0&PaceAdjust=N&PerMode=PerGame&Period=0&PlusMinus=N&Rank=N&Season={season}&SeasonSegment=&SeasonType=Regular+Season&TeamId={team_id}&VsConference=&VsDivision='
RESULT_SET_INDEX = 1
USER_AGENT = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/60.0.3112.101 Safari/537.36'
POSITIONS_ORDER = ['PG', 'SG', 'PF', 'SF', 'C']

NBA_LINEUPS_SNAPSHOT = {
    1610612747: [{'NBA_FANTASY_PTS': 33.9, 'PLAYER_ID': 1628366, 'PLAYER_NAME': 'Lonzo Ball'}, {'NBA_FANTASY_PTS': 28.9, 'PLAYER_ID': 1627742, 'PLAYER_NAME': 'Brandon Ingram'}, {'NBA_FANTASY_PTS': 27.6, 'PLAYER_ID': 1628398, 'PLAYER_NAME': 'Kyle Kuzma'}, {'NBA_FANTASY_PTS': 27.0, 'PLAYER_ID': 203484, 'PLAYER_NAME': 'Kentavious Caldwell-Pope'}, {'NBA_FANTASY_PTS': 26.3, 'PLAYER_ID': 203944, 'PLAYER_NAME': 'Julius Randle'}, {'NBA_FANTASY_PTS': 24.2, 'PLAYER_ID': 1626204, 'PLAYER_NAME': 'Larry Nance Jr.'}, {'NBA_FANTASY_PTS': 23.2, 'PLAYER_ID': 203903, 'PLAYER_NAME': 'Jordan Clarkson'}, {'NBA_FANTASY_PTS': 22.7, 'PLAYER_ID': 201572, 'PLAYER_NAME': 'Brook Lopez'}, {'NBA_FANTASY_PTS': 12.9, 'PLAYER_ID': 1628404, 'PLAYER_NAME': 'Josh Hart'}, {'NBA_FANTASY_PTS': 10.2, 'PLAYER_ID': 1627780, 'PLAYER_NAME': 'Gary Payton II'}, {'NBA_FANTASY_PTS': 9.4, 'PLAYER_ID': 203898, 'PLAYER_NAME': 'Tyler Ennis'}, {'NBA_FANTASY_PTS': 8.7, 'PLAYER_ID': 201147, 'PLAYER_NAME': 'Corey Brewer'}, {'NBA_FANTASY_PTS': 8.0, 'PLAYER_ID': 101106, 'PLAYER_NAME': 'Andrew Bogut'}, {'NBA_FANTASY_PTS': 7.1, 'PLAYER_ID': 1627936, 'PLAYER_NAME': 'Alex Caruso'}, {'NBA_FANTASY_PTS': 5.5, 'PLAYER_ID': 2736, 'PLAYER_NAME': 'Luol Deng'}, {'NBA_FANTASY_PTS': 1.7, 'PLAYER_ID': 203505, 'PLAYER_NAME': 'Vander Blue'}, {'NBA_FANTASY_PTS': 1.6, 'PLAYER_ID': 1627826, 'PLAYER_NAME': 'Ivica Zubac'}, {'NBA_FANTASY_PTS': 1.3, 'PLAYER_ID': 1628418, 'PLAYER_NAME': 'Thomas Bryant'}, {'NBA_FANTASY_PTS': 0.0, 'PLAYER_ID': 1628502, 'PLAYER_NAME': 'Nigel Hayes'}],
1610612752: [{'NBA_FANTASY_PTS': 40.4, 'PLAYER_ID': 204001, 'PLAYER_NAME': 'Kristaps Porzingis'}, {'NBA_FANTASY_PTS': 30.4, 'PLAYER_ID': 203501, 'PLAYER_NAME': 'Tim Hardaway Jr.'}, {'NBA_FANTASY_PTS': 29.1,'PLAYER_ID': 202683, 'PLAYER_NAME': 'Enes Kanter'}, {'NBA_FANTASY_PTS': 24.7, 'PLAYER_ID': 201584, 'PLAYER_NAME': 'Courtney Lee'}, {'NBA_FANTASY_PTS': 21.5, 'PLAYER_ID': 201563, 'PLAYER_NAME': 'Michael Beasley'}, {'NBA_FANTASY_PTS': 21.4, 'PLAYER_ID': 101127, 'PLAYER_NAME': 'Jarrett Jack'}, {'NBA_FANTASY_PTS': 19.9, 'PLAYER_ID': 203124, 'PLAYER_NAME': "Kyle O'Quinn"}, {'NBA_FANTASY_PTS': 15.3, 'PLAYER_ID': 1628373, 'PLAYER_NAME': 'Frank Ntilikina'}, {'NBA_FANTASY_PTS': 12.9, 'PLAYER_ID': 203926, 'PLAYER_NAME': 'Doug McDermott'}, {'NBA_FANTASY_PTS': 10.9, 'PLAYER_ID': 203504, 'PLAYER_NAME': 'Trey Burke'}, {'NBA_FANTASY_PTS': 9.8, 'PLAYER_ID': 1626195, 'PLAYER_NAME': 'Willy Hernangomez'}, {'NBA_FANTASY_PTS': 9.7, 'PLAYER_ID': 1627758, 'PLAYER_NAME': 'Ron Baker'}, {'NBA_FANTASY_PTS': 9.2, 'PLAYER_ID': 201196, 'PLAYER_NAME': 'Ramon Sessions'}, {'NBA_FANTASY_PTS': 9.0, 'PLAYER_ID': 202498, 'PLAYER_NAME': 'Lance Thomas'}, {'NBA_FANTASY_PTS': 6.8, 'PLAYER_ID': 201149, 'PLAYER_NAME': 'Joakim Noah'}, {'NBA_FANTASY_PTS': 5.4, 'PLAYER_ID': 1628422, 'PLAYER_NAME': 'Damyean Dotson'}, {'NBA_FANTASY_PTS': 0.0, 'PLAYER_ID': 1627851, 'PLAYER_NAME': 'Mindaugas Kuzminskas'}],
1610612753: [{'NBA_FANTASY_PTS': 38.0, 'PLAYER_ID': 202696, 'PLAYER_NAME': 'Nikola Vucevic'}, {'NBA_FANTASY_PTS': 34.2, 'PLAYER_ID': 203932, 'PLAYER_NAME': 'Aaron Gordon'}, {'NBA_FANTASY_PTS': 30.2, 'PLAYER_ID': 203901, 'PLAYER_NAME': 'Elfrid Payton'}, {'NBA_FANTASY_PTS': 28.2, 'PLAYER_ID': 203095, 'PLAYER_NAME': 'Evan Fournier'}, {'NBA_FANTASY_PTS': 22.5, 'PLAYER_ID': 203613, 'PLAYER_NAME': 'Jonathon Simmons'}, {'NBA_FANTASY_PTS': 19.1, 'PLAYER_ID': 203082, 'PLAYER_NAME': 'Terrence Ross'}, {'NBA_FANTASY_PTS': 17.1, 'PLAYER_ID': 202687, 'PLAYER_NAME': 'Bismack Biyombo'}, {'NBA_FANTASY_PTS': 15.9, 'PLAYER_ID': 201571, 'PLAYER_NAME': 'D.J. Augustin'}, {'NBA_FANTASY_PTS': 14.8, 'PLAYER_ID': 1628371, 'PLAYER_NAME': 'Jonathan Isaac'}, {'NBA_FANTASY_PTS': 13.5, 'PLAYER_ID': 1626209, 'PLAYER_NAME': 'Mario Hezonja'}, {'NBA_FANTASY_PTS': 12.9, 'PLAYER_ID': 202714, 'PLAYER_NAME': 'Shelvin Mack'}, {'NBA_FANTASY_PTS': 11.9, 'PLAYER_ID': 201578, 'PLAYER_NAME': 'Marreese Speights'}, {'NBA_FANTASY_PTS': 9.3, 'PLAYER_ID': 203920, 'PLAYER_NAME': 'Khem Birch'}, {'NBA_FANTASY_PTS': 8.3, 'PLAYER_ID': 1628411, 'PLAYER_NAME': 'Wes Iwundu'}, {'NBA_FANTASY_PTS': 7.2, 'PLAYER_ID': 203940, 'PLAYER_NAME': 'Adreian Payne'}, {'NBA_FANTASY_PTS': 5.5, 'PLAYER_ID': 201167, 'PLAYER_NAME': 'Arron Afflalo'}, {'NBA_FANTASY_PTS': 4.7, 'PLAYER_ID': 1628503, 'PLAYER_NAME': 'Jamel Artis'}],
1610612739: [{'NBA_FANTASY_PTS': 53.1, 'PLAYER_ID': 2544, 'PLAYER_NAME': 'LeBron James'}, {'NBA_FANTASY_PTS': 34.0, 'PLAYER_ID': 201567, 'PLAYER_NAME': 'Kevin Love'}, {'NBA_FANTASY_PTS': 24.2, 'PLAYER_ID': 2548, 'PLAYER_NAME': 'Dwyane Wade'}, {'NBA_FANTASY_PTS': 21.8, 'PLAYER_ID': 202738, 'PLAYER_NAME': 'Isaiah Thomas'}, {'NBA_FANTASY_PTS': 19.0, 'PLAYER_ID': 201145, 'PLAYER_NAME': 'Jeff Green'}, {'NBA_FANTASY_PTS': 16.9, 'PLAYER_ID': 201565, 'PLAYER_NAME': 'Derrick Rose'}, {'NBA_FANTASY_PTS': 16.6, 'PLAYER_ID': 203109, 'PLAYER_NAME': 'Jae Crowder'}, {'NBA_FANTASY_PTS': 16.2, 'PLAYER_ID': 2747, 'PLAYER_NAME': 'JR Smith'}, {'NBA_FANTASY_PTS': 14.8, 'PLAYER_ID': 2594, 'PLAYER_NAME': 'Kyle Korver'}, {'NBA_FANTASY_PTS': 14.4, 'PLAYER_ID': 202684, 'PLAYER_NAME': 'Tristan Thompson'}, {'NBA_FANTASY_PTS': 11.3, 'PLAYER_ID': 202697, 'PLAYER_NAME': 'Iman Shumpert'}, {'NBA_FANTASY_PTS': 10.0, 'PLAYER_ID': 101181, 'PLAYER_NAME': 'Jose Calderon'}, {'NBA_FANTASY_PTS': 9.0, 'PLAYER_ID':101112, 'PLAYER_NAME': 'Channing Frye'}, {'NBA_FANTASY_PTS': 5.3, 'PLAYER_ID': 1626224, 'PLAYER_NAME': 'Cedi Osman'}, {'NBA_FANTASY_PTS': 3.5, 'PLAYER_ID': 1627790, 'PLAYER_NAME': 'Ante Zizic'},{'NBA_FANTASY_PTS': 1.1, 'PLAYER_ID': 204066, 'PLAYER_NAME': 'John Holland'}, {'NBA_FANTASY_PTS': 0.0, 'PLAYER_ID': 1628506, 'PLAYER_NAME': 'London Perrantes'}],
1610612751: [{'NBA_FANTASY_PTS': 28.9, 'PLAYER_ID': 1626178, 'PLAYER_NAME': 'Rondae Hollis-Jefferson'}, {'NBA_FANTASY_PTS': 28.8, 'PLAYER_ID': 1626156, 'PLAYER_NAME': "D'Angelo Russell"}, {'NBA_FANTASY_PTS': 28.8, 'PLAYER_ID': 203915, 'PLAYER_NAME': 'Spencer Dinwiddie'}, {'NBA_FANTASY_PTS': 26.2, 'PLAYER_ID': 201960, 'PLAYER_NAME': 'DeMarre Carroll'}, {'NBA_FANTASY_PTS': 25.0, 'PLAYER_ID': 1627747,'PLAYER_NAME': 'Caris LeVert'}, {'NBA_FANTASY_PTS': 21.7, 'PLAYER_ID': 202344, 'PLAYER_NAME': 'Trevor Booker'}, {'NBA_FANTASY_PTS': 21.5, 'PLAYER_ID': 203459, 'PLAYER_NAME': 'Allen Crabbe'}, {'NBA_FANTASY_PTS': 21.0, 'PLAYER_ID': 202391, 'PLAYER_NAME': 'Jeremy Lin'}, {'NBA_FANTASY_PTS': 17.2, 'PLAYER_ID': 203925, 'PLAYER_NAME': 'Joe Harris'}, {'NBA_FANTASY_PTS': 15.5, 'PLAYER_ID': 203092, 'PLAYER_NAME': 'Tyler Zeller'}, {'NBA_FANTASY_PTS': 15.2, 'PLAYER_ID': 1628386, 'PLAYER_NAME': 'Jarrett Allen'}, {'NBA_FANTASY_PTS': 13.2, 'PLAYER_ID': 1627785, 'PLAYER_NAME': 'Isaiah Whitehead'}, {'NBA_FANTASY_PTS': 12.6, 'PLAYER_ID': 203112, 'PLAYER_NAME': 'Quincy Acy'}, {'NBA_FANTASY_PTS': 9.4, 'PLAYER_ID': 203917, 'PLAYER_NAME': 'Nik Stauskas'}, {'NBA_FANTASY_PTS': 9.4, 'PLAYER_ID': 202389, 'PLAYER_NAME': 'Timofey Mozgov'}, {'NBA_FANTASY_PTS': 8.9, 'PLAYER_ID': 1626143, 'PLAYER_NAME': 'Jahlil Okafor'}, {'NBA_FANTASY_PTS': 8.5, 'PLAYER_ID': 203930, 'PLAYER_NAME': 'Sean Kilpatrick'}, {'NBA_FANTASY_PTS': 7.0, 'PLAYER_ID': 1628495, 'PLAYER_NAME': 'Milton Doyle'}, {'NBA_FANTASY_PTS': 4.6, 'PLAYER_ID': 1628451, 'PLAYER_NAME': 'Jacob Wiley'}],
1610612758: [{'NBA_FANTASY_PTS': 28.2, 'PLAYER_ID': 1626161, 'PLAYER_NAME': 'Willie Cauley-Stein'}, {'NBA_FANTASY_PTS': 26.4, 'PLAYER_ID': 2216, 'PLAYER_NAME': 'Zach Randolph'}, {'NBA_FANTASY_PTS': 21.5, 'PLAYER_ID': 1627741, 'PLAYER_NAME': 'Buddy Hield'}, {'NBA_FANTASY_PTS': 21.1, 'PLAYER_ID': 1628368, 'PLAYER_NAME': "De'Aaron Fox"}, {'NBA_FANTASY_PTS': 20.9, 'PLAYER_ID': 203992, 'PLAYER_NAME': 'Bogdan Bogdanovic'}, {'NBA_FANTASY_PTS': 20.3, 'PLAYER_ID': 201588, 'PLAYER_NAME': 'George Hill'}, {'NBA_FANTASY_PTS': 17.2, 'PLAYER_ID': 202066, 'PLAYER_NAME': 'Garrett Temple'}, {'NBA_FANTASY_PTS': 17.1, 'PLAYER_ID': 201585, 'PLAYER_NAME': 'Kosta Koufos'}, {'NBA_FANTASY_PTS': 17.1, 'PLAYER_ID': 1627746, 'PLAYER_NAME': 'Skal Labissiere'}, {'NBA_FANTASY_PTS': 15.2, 'PLAYER_ID': 1628412, 'PLAYER_NAME': 'Frank Mason'}, {'NBA_FANTASY_PTS': 14.2, 'PLAYER_ID': 203960, 'PLAYER_NAME': 'JaKarr Sampson'}, {'NBA_FANTASY_PTS': 12.7, 'PLAYER_ID': 1713, 'PLAYER_NAME': 'Vince Carter'}, {'NBA_FANTASY_PTS': 9.1, 'PLAYER_ID': 1628382, 'PLAYER_NAME': 'Justin Jackson'}, {'NBA_FANTASY_PTS': 7.0, 'PLAYER_ID': 1627781, 'PLAYER_NAME': 'Malachi Richardson'}, {'NBA_FANTASY_PTS': 6.7, 'PLAYER_ID': 1627834, 'PLAYER_NAME': 'Georgios Papagiannis'}, {'NBA_FANTASY_PTS': 4.7, 'PLAYER_ID': 204022, 'PLAYER_NAME': 'Jack Cooley'}],
1610612744: [{'NBA_FANTASY_PTS': 48.0, 'PLAYER_ID': 201142, 'PLAYER_NAME': 'Kevin Durant'}, {'NBA_FANTASY_PTS': 45.7, 'PLAYER_ID': 201939, 'PLAYER_NAME': 'Stephen Curry'}, {'NBA_FANTASY_PTS': 37.2, 'PLAYER_ID': 203110, 'PLAYER_NAME': 'Draymond Green'}, {'NBA_FANTASY_PTS': 31.4, 'PLAYER_ID': 202691, 'PLAYER_NAME': 'Klay Thompson'}, {'NBA_FANTASY_PTS': 18.6, 'PLAYER_ID': 2738, 'PLAYER_NAME': 'Andre Iguodala'}, {'NBA_FANTASY_PTS': 17.9, 'PLAYER_ID': 2561, 'PLAYER_NAME': 'David West'}, {'NBA_FANTASY_PTS': 16.7, 'PLAYER_ID': 1628395, 'PLAYER_NAME': 'Jordan Bell'}, {'NBA_FANTASY_PTS': 15.8, 'PLAYER_ID': 201956, 'PLAYER_NAME': 'Omri Casspi'}, {'NBA_FANTASY_PTS': 15.0, 'PLAYER_ID': 2585, 'PLAYER_NAME': 'Zaza Pachulia'}, {'NBA_FANTASY_PTS': 11.8, 'PLAYER_ID': 2733, 'PLAYER_NAME': 'Shaun Livingston'}, {'NBA_FANTASY_PTS': 10.2, 'PLAYER_ID': 1627775, 'PLAYER_NAME': 'Patrick McCaw'}, {'NBA_FANTASY_PTS': 10.1, 'PLAYER_ID': 201156, 'PLAYER_NAME': 'Nick Young'}, {'NBA_FANTASY_PTS': 9.3, 'PLAYER_ID': 201580, 'PLAYER_NAME': 'JaVale McGee'}, {'NBA_FANTASY_PTS': 9.2, 'PLAYER_ID': 1626172, 'PLAYER_NAME': 'Kevon Looney'}, {'NBA_FANTASY_PTS': 6.6, 'PLAYER_ID': 1626188, 'PLAYER_NAME': 'Quinn Cook'}, {'NBA_FANTASY_PTS': 1.2, 'PLAYER_ID': 1627745, 'PLAYER_NAME': 'Damian Jones'}],
1610612759: [{'NBA_FANTASY_PTS': 39.3, 'PLAYER_ID': 200746, 'PLAYER_NAME': 'LaMarcus Aldridge'}, {'NBA_FANTASY_PTS': 32.5, 'PLAYER_ID': 202695, 'PLAYER_NAME': 'Kawhi Leonard'}, {'NBA_FANTASY_PTS': 28.0, 'PLAYER_ID': 2200, 'PLAYER_NAME': 'Pau Gasol'}, {'NBA_FANTASY_PTS': 24.7, 'PLAYER_ID': 203937, 'PLAYER_NAME': 'Kyle Anderson'}, {'NBA_FANTASY_PTS': 22.7, 'PLAYER_ID': 200752, 'PLAYER_NAME': 'Rudy Gay'}, {'NBA_FANTASY_PTS': 20.5, 'PLAYER_ID': 201980, 'PLAYER_NAME': 'Danny Green'}, {'NBA_FANTASY_PTS': 18.3, 'PLAYER_ID': 1627749, 'PLAYER_NAME': 'Dejounte Murray'}, {'NBA_FANTASY_PTS': 17.8, 'PLAYER_ID': 2225, 'PLAYER_NAME': 'Tony Parker'}, {'NBA_FANTASY_PTS': 17.1, 'PLAYER_ID': 201988, 'PLAYER_NAME': 'Patty Mills'}, {'NBA_FANTASY_PTS': 16.6, 'PLAYER_ID': 1938, 'PLAYER_NAME': 'Manu Ginobili'}, {'NBA_FANTASY_PTS': 11.4, 'PLAYER_ID': 1627854, 'PLAYER_NAME': 'Bryn Forbes'}, {'NBA_FANTASY_PTS': 10.6, 'PLAYER_ID': 202722, 'PLAYER_NAME': 'Davis Bertans'}, {'NBA_FANTASY_PTS': 8.6, 'PLAYER_ID': 203530, 'PLAYER_NAME': 'Joffrey Lauvergne'}, {'NBA_FANTASY_PTS': 6.9, 'PLAYER_ID': 203464, 'PLAYER_NAME': 'Brandon Paul'}, {'NBA_FANTASY_PTS': 5.1, 'PLAYER_ID': 1627856, 'PLAYER_NAME': 'Matt Costello'}, {'NBA_FANTASY_PTS': 4.0, 'PLAYER_ID': 1628401, 'PLAYER_NAME': 'Derrick White'}, {'NBA_FANTASY_PTS': 2.4, 'PLAYER_ID': 1626199, 'PLAYER_NAME': 'Darrun Hilliard'}],
1610612738 :[{'NBA_FANTASY_PTS': 38.5, 'PLAYER_ID': 202681, 'PLAYER_NAME': 'Kyrie Irving'}, {'NBA_FANTASY_PTS': 33.6, 'PLAYER_ID': 201143, 'PLAYER_NAME': 'Al Horford'}, {'NBA_FANTASY_PTS': 26.4, 'PLAYER_ID': 1628369, 'PLAYER_NAME': 'Jayson Tatum'}, {'NBA_FANTASY_PTS': 26.1, 'PLAYER_ID': 1627759, 'PLAYER_NAME': 'Jaylen Brown'}, {'NBA_FANTASY_PTS': 23.8, 'PLAYER_ID': 203935, 'PLAYER_NAME': 'Marcus Smart'}, {'NBA_FANTASY_PTS': 21.3, 'PLAYER_ID': 202694, 'PLAYER_NAME': 'Marcus Morris'}, {'NBA_FANTASY_PTS': 19.9, 'PLAYER_ID': 1626179, 'PLAYER_NAME': 'Terry Rozier'}, {'NBA_FANTASY_PTS': 15.1, 'PLAYER_ID': 203382, 'PLAYER_NAME': 'Aron Baynes'}, {'NBA_FANTASY_PTS': 13.2, 'PLAYER_ID': 1628464, 'PLAYER_NAME': 'Daniel Theis'}, {'NBA_FANTASY_PTS': 7.2, 'PLAYER_ID': 203499, 'PLAYER_NAME': 'Shane Larkin'}, {'NBA_FANTASY_PTS': 5.4, 'PLAYER_ID': 1628400, 'PLAYER_NAME': 'Semi Ojeleye'}, {'NBA_FANTASY_PTS': 4.3, 'PLAYER_ID': 1627846, 'PLAYER_NAME': 'Abdel Nader'}, {'NBA_FANTASY_PTS': 3.7, 'PLAYER_ID': 1627824, 'PLAYER_NAME': 'Guerschon Yabusele'}, {'NBA_FANTASY_PTS': 3.2, 'PLAYER_ID': 202330, 'PLAYER_NAME': 'Gordon Hayward'}, {'NBA_FANTASY_PTS': 3.0, 'PLAYER_ID': 1628444, 'PLAYER_NAME': 'Jabari Bird'}, {'NBA_FANTASY_PTS': 1.5, 'PLAYER_ID': 1628443, 'PLAYER_NAME': 'Kadeem Allen'}],
1610612760: [{'NBA_FANTASY_PTS': 53.5, 'PLAYER_ID': 201566, 'PLAYER_NAME': 'Russell Westbrook'}, {'NBA_FANTASY_PTS': 37.5, 'PLAYER_ID': 202331, 'PLAYER_NAME': 'Paul George'}, {'NBA_FANTASY_PTS': 30.9, 'PLAYER_ID': 203500, 'PLAYER_NAME': 'Steven Adams'}, {'NBA_FANTASY_PTS': 29.5, 'PLAYER_ID': 2546, 'PLAYER_NAME': 'Carmelo Anthony'}, {'NBA_FANTASY_PTS': 17.7, 'PLAYER_ID': 203460, 'PLAYER_NAME': 'Andre Roberson'}, {'NBA_FANTASY_PTS': 15.9, 'PLAYER_ID': 203924, 'PLAYER_NAME': 'Jerami Grant'}, {'NBA_FANTASY_PTS': 14.9, 'PLAYER_ID': 101109, 'PLAYER_NAME': 'Raymond Felton'}, {'NBA_FANTASY_PTS': 8.6, 'PLAYER_ID': 1627772, 'PLAYER_NAME': 'Daniel Hamilton'}, {'NBA_FANTASY_PTS': 8.5, 'PLAYER_ID': 202335, 'PLAYER_NAME': 'Patrick Patterson'}, {'NBA_FANTASY_PTS': 8.2, 'PLAYER_ID': 203518, 'PLAYER_NAME': 'Alex Abrines'}, {'NBA_FANTASY_PTS': 8.2, 'PLAYER_ID': 203962, 'PLAYER_NAME': 'Josh Huestis'}, {'NBA_FANTASY_PTS': 5.7, 'PLAYER_ID': 1628390, 'PLAYER_NAME': 'Terrance Ferguson'}, {'NBA_FANTASY_PTS': 5.6, 'PLAYER_ID': 1626177, 'PLAYER_NAME': 'Dakari Johnson'}, {'NBA_FANTASY_PTS': 3.6, 'PLAYER_ID': 2555, 'PLAYER_NAME': 'Nick Collison'}, {'NBA_FANTASY_PTS': 3.3, 'PLAYER_ID': 202713, 'PLAYER_NAME': 'Kyle Singler'}],
1610612742: [{'PLAYER_NAME': 'Harrison Barnes', 'NBA_FANTASY_PTS': 30.9, 'PLAYER_ID': 203084}, {'PLAYER_NAME': 'Dennis Smith Jr.', 'NBA_FANTASY_PTS': 27.4, 'PLAYER_ID': 1628372}, {'PLAYER_NAME': 'J.J. Barea', 'NBA_FANTASY_PTS': 24.1, 'PLAYER_ID': 200826}, {'PLAYER_NAME': 'Dirk Nowitzki', 'NBA_FANTASY_PTS': 23.8, 'PLAYER_ID': 1717}, {'PLAYER_NAME': 'Wesley Matthews', 'NBA_FANTASY_PTS': 22.9, 'PLAYER_ID': 202083}, {'PLAYER_NAME': 'Yogi Ferrell', 'NBA_FANTASY_PTS': 19.3, 'PLAYER_ID': 1627812}, {'PLAYER_NAME': 'Dwight Powell', 'NBA_FANTASY_PTS': 17.0, 'PLAYER_ID': 203939}, {'PLAYER_NAME': 'Devin Harris', 'NBA_FANTASY_PTS': 15.2, 'PLAYER_ID': 2734}, {'PLAYER_NAME': 'Maxi Kleber', 'NBA_FANTASY_PTS': 13.1, 'PLAYER_ID': 1628467}, {'PLAYER_NAME': 'Salah Mejri', 'NBA_FANTASY_PTS': 13.0, 'PLAYER_ID': 1626257}, {'PLAYER_NAME': 'Nerlens Noel', 'NBA_FANTASY_PTS': 11.9, 'PLAYER_ID': 203457}, {'PLAYER_NAME': 'Johnathan Motley', 'NBA_FANTASY_PTS': 8.2, 'PLAYER_ID': 1628405}, {'PLAYER_NAME': 'Kyle Collinsworth', 'NBA_FANTASY_PTS': 5.7, 'PLAYER_ID': 1627858}, {'PLAYER_NAME': 'Gian Clavell', 'NBA_FANTASY_PTS': 5.3, 'PLAYER_ID': 1628492}, {'PLAYER_NAME': 'Dorian Finney-Smith', 'NBA_FANTASY_PTS': 5.2, 'PLAYER_ID': 1627827}, {'PLAYER_NAME': 'Antonius Cleveland', 'NBA_FANTASY_PTS': 4.1, 'PLAYER_ID': 1628499}, {'PLAYER_NAME': 'Jeff Withey', 'NBA_FANTASY_PTS': 3.8, 'PLAYER_ID': 203481}, {'PLAYER_NAME': 'Jalen Jones', 'NBA_FANTASY_PTS': 2.0, 'PLAYER_ID': 1627883}, {'PLAYER_NAME': 'Josh McRoberts', 'NBA_FANTASY_PTS': 0.0, 'PLAYER_ID': 201177}],
1610612754: [{'PLAYER_NAME': 'Victor Oladipo', 'NBA_FANTASY_PTS': 41.9, 'PLAYER_ID': 203506}, {'PLAYER_NAME': 'Myles Turner', 'NBA_FANTASY_PTS': 30.6, 'PLAYER_ID': 1626167}, {'PLAYER_NAME': 'Darren Collison', 'NBA_FANTASY_PTS': 27.0, 'PLAYER_ID': 201954}, {'PLAYER_NAME': 'Thaddeus Young', 'NBA_FANTASY_PTS': 26.6, 'PLAYER_ID': 201152}, {'PLAYER_NAME': 'Domantas Sabonis', 'NBA_FANTASY_PTS': 26.1, 'PLAYER_ID': 1627734}, {'PLAYER_NAME': 'Lance Stephenson', 'NBA_FANTASY_PTS': 20.1, 'PLAYER_ID': 202362}, {'PLAYER_NAME': 'Bojan Bogdanovic', 'NBA_FANTASY_PTS': 20.0, 'PLAYER_ID': 202711}, {'PLAYER_NAME': 'Cory Joseph', 'NBA_FANTASY_PTS': 18.2, 'PLAYER_ID': 202709}, {'PLAYER_NAME': 'Al Jefferson', 'NBA_FANTASY_PTS': 15.8, 'PLAYER_ID': 2744}, {'PLAYER_NAME': 'Joe Young', 'NBA_FANTASY_PTS': 6.2, 'PLAYER_ID': 1626202}, {'PLAYER_NAME': 'TJ Leaf', 'NBA_FANTASY_PTS': 5.9, 'PLAYER_ID': 1628388}, {'PLAYER_NAME': 'Damien Wilkins', 'NBA_FANTASY_PTS': 3.7, 'PLAYER_ID': 2863}, {'PLAYER_NAME': 'Ike Anigbogu', 'NBA_FANTASY_PTS': 3.4, 'PLAYER_ID': 1628387}, {'PLAYER_NAME': 'Alex Poythress', 'NBA_FANTASY_PTS': 2.1, 'PLAYER_ID': 1627816}],
1610612766: [{'PLAYER_NAME': 'Kemba Walker', 'NBA_FANTASY_PTS': 37.2, 'PLAYER_ID': 202689}, {'PLAYER_NAME': 'Dwight Howard', 'NBA_FANTASY_PTS': 36.3, 'PLAYER_ID': 2730}, {'PLAYER_NAME': 'Jeremy Lamb', 'NBA_FANTASY_PTS': 25.7, 'PLAYER_ID': 203087}, {'PLAYER_NAME': 'Nicolas Batum', 'NBA_FANTASY_PTS': 24.8, 'PLAYER_ID': 201587}, {'PLAYER_NAME': 'Michael Kidd-Gilchrist', 'NBA_FANTASY_PTS': 21.4, 'PLAYER_ID': 203077}, {'PLAYER_NAME': 'Frank Kaminsky', 'NBA_FANTASY_PTS': 19.2, 'PLAYER_ID': 1626163}, {'PLAYER_NAME': 'Marvin Williams', 'NBA_FANTASY_PTS': 19.1, 'PLAYER_ID': 101107}, {'PLAYER_NAME':'Cody Zeller', 'NBA_FANTASY_PTS': 18.7, 'PLAYER_ID': 203469}, {'PLAYER_NAME': 'Michael Carter-Williams', 'NBA_FANTASY_PTS': 13.0, 'PLAYER_ID': 203487}, {'PLAYER_NAME': 'Treveon Graham', 'NBA_FANTASY_PTS': 10.1, 'PLAYER_ID': 1626203}, {'PLAYER_NAME': "Johnny O'Bryant III", 'NBA_FANTASY_PTS': 10.0, 'PLAYER_ID': 203948}, {'PLAYER_NAME': 'Malik Monk', 'NBA_FANTASY_PTS': 9.0, 'PLAYER_ID': 1628370}, {'PLAYER_NAME': 'Dwayne Bacon', 'NBA_FANTASY_PTS': 8.3, 'PLAYER_ID': 1628407}, {'PLAYER_NAME': 'Julyan Stone', 'NBA_FANTASY_PTS': 5.0, 'PLAYER_ID': 202933}, {'PLAYER_NAME': 'Mangok Mathiang', 'NBA_FANTASY_PTS': 2.4, 'PLAYER_ID': 1628493}, {'PLAYER_NAME': 'Marcus Paige', 'NBA_FANTASY_PTS': 2.4, 'PLAYER_ID': 1627779}],
1610612765: [{'PLAYER_NAME': 'Andre Drummond', 'NBA_FANTASY_PTS': 43.8, 'PLAYER_ID': 203083}, {'PLAYER_NAME': 'Tobias Harris', 'NBA_FANTASY_PTS': 29.4, 'PLAYER_ID': 202699}, {'PLAYER_NAME': 'Reggie Jackson', 'NBA_FANTASY_PTS': 25.9, 'PLAYER_ID': 202704}, {'PLAYER_NAME': 'Avery Bradley', 'NBA_FANTASY_PTS': 23.2, 'PLAYER_ID': 202340}, {'PLAYER_NAME': 'Ish Smith', 'NBA_FANTASY_PTS': 20.9, 'PLAYER_ID':202397}, {'PLAYER_NAME': 'Stanley Johnson', 'NBA_FANTASY_PTS': 17.2, 'PLAYER_ID': 1626169}, {'PLAYER_NAME': 'Reggie Bullock', 'NBA_FANTASY_PTS': 14.0, 'PLAYER_ID': 203493}, {'PLAYER_NAME': 'Dwight Buycks', 'NBA_FANTASY_PTS': 13.1, 'PLAYER_ID': 202779}, {'PLAYER_NAME': 'Anthony Tolliver', 'NBA_FANTASY_PTS': 13.0, 'PLAYER_ID': 201229}, {'PLAYER_NAME': 'Luke Kennard', 'NBA_FANTASY_PTS': 12.7, 'PLAYER_ID': 1628379}, {'PLAYER_NAME': 'Langston Galloway', 'NBA_FANTASY_PTS': 11.8, 'PLAYER_ID': 204038}, {'PLAYER_NAME': 'Jon Leuer', 'NBA_FANTASY_PTS': 11.6, 'PLAYER_ID': 202720}, {'PLAYER_NAME': 'Boban Marjanovic', 'NBA_FANTASY_PTS': 10.2, 'PLAYER_ID': 1626246}, {'PLAYER_NAME': 'Eric Moreland', 'NBA_FANTASY_PTS': 10.1, 'PLAYER_ID': 203961}, {'PLAYER_NAME': 'Henry Ellenson', 'NBA_FANTASY_PTS': 5.8, 'PLAYER_ID': 1627740}, {'PLAYER_NAME': 'Luis Montero', 'NBA_FANTASY_PTS': 0.2, 'PLAYER_ID': 1626242}],
1610612740: [{'PLAYER_NAME': 'DeMarcus Cousins', 'NBA_FANTASY_PTS': 53.5, 'PLAYER_ID': 202326}, {'PLAYER_NAME': 'Anthony Davis', 'NBA_FANTASY_PTS': 50.4, 'PLAYER_ID': 203076}, {'PLAYER_NAME': 'Jrue Holiday', 'NBA_FANTASY_PTS': 35.3, 'PLAYER_ID': 201950}, {'PLAYER_NAME': 'Rajon Rondo', 'NBA_FANTASY_PTS': 23.7, 'PLAYER_ID': 200765}, {'PLAYER_NAME': "E'Twaun Moore", 'NBA_FANTASY_PTS': 21.7, 'PLAYER_ID': 202734}, {'PLAYER_NAME': 'Jordan Crawford', 'NBA_FANTASY_PTS': 17.1, 'PLAYER_ID': 202348}, {'PLAYER_NAME': 'Jameer Nelson', 'NBA_FANTASY_PTS': 13.9, 'PLAYER_ID': 2749}, {'PLAYER_NAME': 'DariusMiller', 'NBA_FANTASY_PTS': 12.6, 'PLAYER_ID': 203121}, {'PLAYER_NAME': 'Dante Cunningham', 'NBA_FANTASY_PTS': 12.4, 'PLAYER_ID': 201967}, {'PLAYER_NAME': 'Ian Clark', 'NBA_FANTASY_PTS': 9.8, 'PLAYER_ID': 203546}, {'PLAYER_NAME': 'Tony Allen', 'NBA_FANTASY_PTS': 8.9, 'PLAYER_ID': 2754}, {'PLAYER_NAME': 'DeAndre Liggins', 'NBA_FANTASY_PTS': 6.7, 'PLAYER_ID': 202732}, {'PLAYER_NAME': 'Cheick Diallo', 'NBA_FANTASY_PTS': 5.5, 'PLAYER_ID': 1627767}, {'PLAYER_NAME': 'Omer Asik', 'NBA_FANTASY_PTS': 4.4, 'PLAYER_ID': 201600}, {'PLAYER_NAME': 'Josh Smith', 'NBA_FANTASY_PTS': 2.3, 'PLAYER_ID': 2746}, {'PLAYER_NAME': 'Jalen Jones', 'NBA_FANTASY_PTS': 2.2, 'PLAYER_ID': 1627883}, {'PLAYER_NAME': 'Charles Cooke', 'NBA_FANTASY_PTS': 1.6, 'PLAYER_ID': 1628429}],
1610612745: [{'NBA_FANTASY_PTS': 53.4, 'PLAYER_NAME': 'James Harden', 'PLAYER_ID': 201935}, {'NBA_FANTASY_PTS': 43.9, 'PLAYER_NAME': 'Chris Paul', 'PLAYER_ID': 101108}, {'NBA_FANTASY_PTS': 34.9, 'PLAYER_NAME': 'Clint Capela', 'PLAYER_ID': 203991}, {'NBA_FANTASY_PTS': 27.2, 'PLAYER_NAME': 'Eric Gordon', 'PLAYER_ID': 201569}, {'NBA_FANTASY_PTS': 24.9, 'PLAYER_NAME': 'Trevor Ariza', 'PLAYER_ID': 2772}, {'NBA_FANTASY_PTS': 22.8, 'PLAYER_NAME': 'Gerald Green', 'PLAYER_ID': 101123}, {'NBA_FANTASY_PTS': 20.2, 'PLAYER_NAME': 'Ryan Anderson', 'PLAYER_ID': 201583}, {'NBA_FANTASY_PTS': 17.0, 'PLAYER_NAME': 'PJ Tucker', 'PLAYER_ID': 200782}, {'NBA_FANTASY_PTS': 16.7, 'PLAYER_NAME': 'Luc Mbah a Moute', 'PLAYER_ID': 201601}, {'NBA_FANTASY_PTS': 14.5, 'PLAYER_NAME': 'Nene', 'PLAYER_ID': 2403}, {'NBA_FANTASY_PTS': 9.8, 'PLAYER_NAME': 'Tarik Black', 'PLAYER_ID': 204028}, {'NBA_FANTASY_PTS': 7.6, 'PLAYER_NAME': 'Briante Weber', 'PLAYER_ID': 1627362}, {'NBA_FANTASY_PTS': 3.9, 'PLAYER_NAME':'Bobby Brown', 'PLAYER_ID': 201628}, {'NBA_FANTASY_PTS': 3.8, 'PLAYER_NAME': 'Zhou Qi', 'PLAYER_ID': 1627753}, {'NBA_FANTASY_PTS': 3.3, 'PLAYER_NAME': 'Troy Williams', 'PLAYER_ID': 1627786}, {'NBA_FANTASY_PTS': 2.8, 'PLAYER_NAME': 'Demetrius Jackson', 'PLAYER_ID': 1627743}, {'NBA_FANTASY_PTS': 2.1, 'PLAYER_NAME': 'RJ Hunter', 'PLAYER_ID': 1626154}, {'NBA_FANTASY_PTS': 1.2, 'PLAYER_NAME': 'Isaiah Canaan', 'PLAYER_ID': 203477}],
1610612762: [{'NBA_FANTASY_PTS': 32.3, 'PLAYER_NAME': 'Rudy Gobert', 'PLAYER_ID': 203497}, {'NBA_FANTASY_PTS': 31.4, 'PLAYER_NAME': 'Donovan Mitchell', 'PLAYER_ID': 1628378}, {'NBA_FANTASY_PTS': 26.6, 'PLAYER_NAME': 'Derrick Favors', 'PLAYER_ID': 202324}, {'NBA_FANTASY_PTS': 25.5, 'PLAYER_NAME': 'Ricky Rubio', 'PLAYER_ID': 201937}, {'NBA_FANTASY_PTS': 24.0, 'PLAYER_NAME': 'Rodney Hood', 'PLAYER_ID': 203918}, {'NBA_FANTASY_PTS': 22.9, 'PLAYER_NAME': 'Joe Ingles', 'PLAYER_ID': 204060}, {'NBA_FANTASY_PTS': 18.9, 'PLAYER_NAME': 'Thabo Sefolosha', 'PLAYER_ID': 200757}, {'NBA_FANTASY_PTS': 17.0,'PLAYER_NAME': 'Alec Burks', 'PLAYER_ID': 202692}, {'NBA_FANTASY_PTS': 14.4, 'PLAYER_NAME': 'Ekpe Udoh', 'PLAYER_ID': 202327}, {'NBA_FANTASY_PTS': 14.1, 'PLAYER_NAME': 'Joe Johnson', 'PLAYER_ID': 2207}, {'NBA_FANTASY_PTS': 12.9, 'PLAYER_NAME': 'Jonas Jerebko', 'PLAYER_ID': 201973}, {'NBA_FANTASY_PTS': 10.1, 'PLAYER_NAME': 'Raul Neto', 'PLAYER_ID': 203526}, {'NBA_FANTASY_PTS': 9.1, 'PLAYER_NAME': "Royce O'Neale", 'PLAYER_ID': 1626220}, {'NBA_FANTASY_PTS': 3.0, 'PLAYER_NAME': 'Naz Mitrou-Long', 'PLAYER_ID': 1628513}, {'NBA_FANTASY_PTS': 2.8, 'PLAYER_NAME': 'Tony Bradley', 'PLAYER_ID': 1628396}, {'NBA_FANTASY_PTS': 1.2, 'PLAYER_NAME': 'Nate Wolters', 'PLAYER_ID': 203489}],
1610612757: [{'NBA_FANTASY_PTS': 41.9, 'PLAYER_NAME': 'Damian Lillard', 'PLAYER_ID': 203081}, {'NBA_FANTASY_PTS': 33.5, 'PLAYER_NAME': 'CJ McCollum', 'PLAYER_ID': 203468}, {'NBA_FANTASY_PTS': 30.6, 'PLAYER_NAME': 'Jusuf Nurkic', 'PLAYER_ID': 203994}, {'NBA_FANTASY_PTS': 23.3, 'PLAYER_NAME': 'Al-Farouq Aminu', 'PLAYER_ID': 202329}, {'NBA_FANTASY_PTS': 19.7, 'PLAYER_NAME': 'Shabazz Napier', 'PLAYER_ID': 203894}, {'NBA_FANTASY_PTS': 17.6, 'PLAYER_NAME': 'Evan Turner', 'PLAYER_ID': 202323}, {'NBA_FANTASY_PTS': 16.6, 'PLAYER_NAME': 'Ed Davis', 'PLAYER_ID': 202334}, {'NBA_FANTASY_PTS': 13.4, 'PLAYER_NAME': 'Maurice Harkless', 'PLAYER_ID': 203090}, {'NBA_FANTASY_PTS': 12.8, 'PLAYER_NAME': 'Noah Vonleh', 'PLAYER_ID': 203943}, {'NBA_FANTASY_PTS': 12.0, 'PLAYER_NAME': 'Pat Connaughton', 'PLAYER_ID': 1626192}, {'NBA_FANTASY_PTS': 10.5, 'PLAYER_NAME': 'Zach Collins', 'PLAYER_ID': 1628380}, {'NBA_FANTASY_PTS': 9.0, 'PLAYER_NAME': 'Meyers Leonard', 'PLAYER_ID': 203086}, {'NBA_FANTASY_PTS': 7.2, 'PLAYER_NAME': 'Caleb Swanigan', 'PLAYER_ID': 1628403}, {'NBA_FANTASY_PTS': 3.3, 'PLAYER_NAME': 'Jake Layman', 'PLAYER_ID': 1627774}],
1610612756: [{'NBA_FANTASY_PTS': 37.6, 'PLAYER_NAME': 'Devin Booker', 'PLAYER_ID': 1626164}, {'NBA_FANTASY_PTS': 32.0, 'PLAYER_NAME': 'TJ Warren', 'PLAYER_ID': 203933}, {'NBA_FANTASY_PTS': 26.0, 'PLAYER_NAME': 'Greg Monroe', 'PLAYER_ID': 202328}, {'NBA_FANTASY_PTS': 25.6, 'PLAYER_NAME': 'Eric Bledsoe', 'PLAYER_ID': 202339}, {'NBA_FANTASY_PTS': 22.4, 'PLAYER_NAME': 'Alex Len', 'PLAYER_ID': 203458}, {'NBA_FANTASY_PTS': 21.8, 'PLAYER_NAME': 'Isaiah Canaan', 'PLAYER_ID': 203477}, {'NBA_FANTASY_PTS': 21.6, 'PLAYER_NAME': 'Tyson Chandler', 'PLAYER_ID': 2199}, {'NBA_FANTASY_PTS': 21.0, 'PLAYER_NAME': 'Mike James', 'PLAYER_ID': 1628455}, {'NBA_FANTASY_PTS': 18.8, 'PLAYER_NAME': 'Marquese Chriss', 'PLAYER_ID': 1627737}, {'NBA_FANTASY_PTS': 17.7, 'PLAYER_NAME': 'Josh Jackson', 'PLAYER_ID': 1628367}, {'NBA_FANTASY_PTS': 17.3, 'PLAYER_NAME': 'Tyler Ulis', 'PLAYER_ID': 1627755}, {'NBA_FANTASY_PTS': 13.1, 'PLAYER_NAME': 'Dragan Bender', 'PLAYER_ID': 1627733}, {'NBA_FANTASY_PTS': 11.0, 'PLAYER_NAME': 'Troy Daniels', 'PLAYER_ID': 203584}, {'NBA_FANTASY_PTS': 9.9, 'PLAYER_NAME': 'Jared Dudley', 'PLAYER_ID': 201162}, {'NBA_FANTASY_PTS': 8.5, 'PLAYER_NAME': 'Danuel House', 'PLAYER_ID': 1627863}, {'NBA_FANTASY_PTS': 6.7, 'PLAYER_NAME': 'Alec Peters', 'PLAYER_ID': 1628409}, {'NBA_FANTASY_PTS': 5.4, 'PLAYER_NAME': 'Derrick Jones Jr.', 'PLAYER_ID': 1627884}, {'NBA_FANTASY_PTS': 1.2, 'PLAYER_NAME': 'Davon Reed', 'PLAYER_ID': 1628432}],
1610612755: [{'NBA_FANTASY_PTS': 45.4, 'PLAYER_NAME': 'Joel Embiid', 'PLAYER_ID': 203954}, {'NBA_FANTASY_PTS': 40.9, 'PLAYER_NAME': 'Ben Simmons', 'PLAYER_ID': 1627732}, {'NBA_FANTASY_PTS': 28.8, 'PLAYER_NAME': 'Robert Covington', 'PLAYER_ID': 203496}, {'NBA_FANTASY_PTS': 27.3, 'PLAYER_NAME': 'Dario Saric', 'PLAYER_ID': 203967}, {'NBA_FANTASY_PTS': 26.0, 'PLAYER_NAME': 'JJ Redick', 'PLAYER_ID': 200755}, {'NBA_FANTASY_PTS': 21.9, 'PLAYER_NAME': 'T.J. McConnell', 'PLAYER_ID': 204456}, {'NBA_FANTASY_PTS': 16.2, 'PLAYER_NAME': 'Richaun Holmes', 'PLAYER_ID': 1626158}, {'NBA_FANTASY_PTS': 16.0, 'PLAYER_NAME': 'Amir Johnson', 'PLAYER_ID': 101161}, {'NBA_FANTASY_PTS': 14.4, 'PLAYER_NAME': 'Jerryd Bayless', 'PLAYER_ID': 201573}, {'NBA_FANTASY_PTS': 12.8, 'PLAYER_NAME': 'Trevor Booker', 'PLAYER_ID': 202344}, {'NBA_FANTASY_PTS': 12.7, 'PLAYER_NAME': 'Jahlil Okafor', 'PLAYER_ID': 1626143}, {'NBA_FANTASY_PTS': 12.1, 'PLAYER_NAME': 'Markelle Fultz', 'PLAYER_ID': 1628365}, {'NBA_FANTASY_PTS': 10.1, 'PLAYER_NAME': 'Timothe Luwawu-Cabarrot', 'PLAYER_ID': 1627789}, {'NBA_FANTASY_PTS': 8.7, 'PLAYER_NAME': 'Justin Anderson', 'PLAYER_ID': 1626147}, {'NBA_FANTASY_PTS': 4.1, 'PLAYER_NAME': 'James Michael McAdoo', 'PLAYER_ID': 203949}, {'NBA_FANTASY_PTS': 4.0, 'PLAYER_NAME': 'James Young', 'PLAYER_ID': 203923}, {'NBA_FANTASY_PTS': 3.5, 'PLAYER_NAME': 'Furkan Korkmaz', 'PLAYER_ID': 1627788}, {'NBA_FANTASY_PTS': 2.5, 'PLAYER_NAME': 'Nik Stauskas', 'PLAYER_ID': 203917}, {'NBA_FANTASY_PTS': 0.3, 'PLAYER_NAME': 'Jacob Pullen', 'PLAYER_ID': 1626643}],
1610612763: [{'NBA_FANTASY_PTS': 37.7, 'PLAYER_NAME': 'Marc Gasol', 'PLAYER_ID': 201188}, {'NBA_FANTASY_PTS': 35.0, 'PLAYER_NAME': 'Tyreke Evans', 'PLAYER_ID': 201936}, {'NBA_FANTASY_PTS': 28.2, 'PLAYER_NAME': 'Mike Conley', 'PLAYER_ID': 201144}, {'NBA_FANTASY_PTS': 22.1, 'PLAYER_NAME': 'JaMychal Green', 'PLAYER_ID': 203210}, {'NBA_FANTASY_PTS': 18.2, 'PLAYER_NAME': 'Mario Chalmers', 'PLAYER_ID': 201596}, {'NBA_FANTASY_PTS': 16.7, 'PLAYER_NAME': 'Chandler Parsons', 'PLAYER_ID': 202718}, {'NBA_FANTASY_PTS': 15.8, 'PLAYER_NAME': 'Andrew Harrison', 'PLAYER_ID': 1626150}, {'NBA_FANTASY_PTS': 15.7, 'PLAYER_NAME': 'Dillon Brooks', 'PLAYER_ID': 1628415}, {'NBA_FANTASY_PTS': 14.7, 'PLAYER_NAME': 'James Ennis III', 'PLAYER_ID': 203516}, {'NBA_FANTASY_PTS': 14.6, 'PLAYER_NAME': 'Myke Henry', 'PLAYER_ID': 1627988}, {'NBA_FANTASY_PTS': 14.1, 'PLAYER_NAME': 'Brandan Wright', 'PLAYER_ID': 201148}, {'NBA_FANTASY_PTS': 14.0, 'PLAYER_NAME': 'Jarell Martin', 'PLAYER_ID': 1626185}, {'NBA_FANTASY_PTS': 11.7, 'PLAYER_NAME': 'Deyonta Davis', 'PLAYER_ID': 1627738}, {'NBA_FANTASY_PTS': 11.7, 'PLAYER_NAME': 'Wayne Selden', 'PLAYER_ID': 1627782}, {'NBA_FANTASY_PTS': 11.6, 'PLAYER_NAME': 'Ben McLemore', 'PLAYER_ID': 203463}, {'NBA_FANTASY_PTS': 8.8, 'PLAYER_NAME': 'Kobi Simmons', 'PLAYER_ID': 1628424}, {'NBA_FANTASY_PTS': 5.0, 'PLAYER_NAME': 'Ivan Rabb', 'PLAYER_ID': 1628397}, {'NBA_FANTASY_PTS': 2.9, 'PLAYER_NAME': 'Vincent Hunter', 'PLAYER_ID': 1626205}],
1610612741: [{'NBA_FANTASY_PTS': 33.3, 'PLAYER_NAME': 'Kris Dunn', 'PLAYER_ID': 1627739}, {'NBA_FANTASY_PTS': 29.6, 'PLAYER_NAME': 'Nikola Mirotic', 'PLAYER_ID': 202703}, {'NBA_FANTASY_PTS': 28.9, 'PLAYER_NAME': 'Lauri Markkanen', 'PLAYER_ID': 1628374}, {'NBA_FANTASY_PTS': 26.5, 'PLAYER_NAME': 'Justin Holiday', 'PLAYER_ID': 203200}, {'NBA_FANTASY_PTS': 23.5, 'PLAYER_NAME': 'Robin Lopez', 'PLAYER_ID': 201577}, {'NBA_FANTASY_PTS': 22.7, 'PLAYER_NAME': 'Bobby Portis', 'PLAYER_ID': 1626171}, {'NBA_FANTASY_PTS': 22.3, 'PLAYER_NAME': 'Denzel Valentine', 'PLAYER_ID': 1627756}, {'NBA_FANTASY_PTS':22.1, 'PLAYER_NAME': 'Zach LaVine', 'PLAYER_ID': 203897}, {'NBA_FANTASY_PTS': 19.3, 'PLAYER_NAME': 'Jerian Grant', 'PLAYER_ID': 1626170}, {'NBA_FANTASY_PTS': 17.7, 'PLAYER_NAME': 'David Nwaba', 'PLAYER_ID': 1628021}, {'NBA_FANTASY_PTS': 10.0, 'PLAYER_NAME': 'Antonio Blakeney', 'PLAYER_ID': 1628469}, {'NBA_FANTASY_PTS': 8.6, 'PLAYER_NAME': 'Paul Zipser', 'PLAYER_ID': 1627835}, {'NBA_FANTASY_PTS': 8.5, 'PLAYER_NAME': 'Cristiano Felicio', 'PLAYER_ID': 1626245}, {'NBA_FANTASY_PTS': 7.1, 'PLAYER_NAME': 'Kay Felder', 'PLAYER_ID': 1627770}, {'NBA_FANTASY_PTS': 6.2, 'PLAYER_NAME': 'Ryan Arcidiacono', 'PLAYER_ID': 1627853}, {'NBA_FANTASY_PTS': 5.1, 'PLAYER_NAME': 'Quincy Pondexter', 'PLAYER_ID': 202347}],
1610612746: [{'NBA_FANTASY_PTS': 40.7, 'PLAYER_NAME': 'Blake Griffin', 'PLAYER_ID': 201933}, {'NBA_FANTASY_PTS': 34.7, 'PLAYER_NAME': 'Lou Williams', 'PLAYER_ID': 101150}, {'NBA_FANTASY_PTS': 34.2, 'PLAYER_NAME': 'DeAndre Jordan', 'PLAYER_ID': 201599}, {'NBA_FANTASY_PTS': 26.3, 'PLAYER_NAME': 'Austin Rivers', 'PLAYER_ID': 203085}, {'NBA_FANTASY_PTS': 25.7, 'PLAYER_NAME': 'Patrick Beverley', 'PLAYER_ID': 201976}, {'NBA_FANTASY_PTS': 23.8, 'PLAYER_NAME': 'Tyrone Wallace', 'PLAYER_ID': 1627820}, {'NBA_FANTASY_PTS': 23.7, 'PLAYER_NAME': 'Danilo Gallinari', 'PLAYER_ID': 201568}, {'NBA_FANTASY_PTS': 21.0, 'PLAYER_NAME': 'Milos Teodosic', 'PLAYER_ID': 1628462}, {'NBA_FANTASY_PTS': 18.3, 'PLAYER_NAME': 'Wesley Johnson', 'PLAYER_ID': 202325}, {'NBA_FANTASY_PTS': 16.6, 'PLAYER_NAME': 'Montrezl Harrell', 'PLAYER_ID': 1626149}, {'NBA_FANTASY_PTS': 13.7, 'PLAYER_NAME': 'Jawun Evans', 'PLAYER_ID': 1628393}, {'NBA_FANTASY_PTS': 12.6, 'PLAYER_NAME': 'Jamil Wilson', 'PLAYER_ID': 203966}, {'NBA_FANTASY_PTS': 12.5, 'PLAYER_NAME': 'C.J. Williams', 'PLAYER_ID': 203710}, {'NBA_FANTASY_PTS': 11.1, 'PLAYER_NAME': 'Willie Reed', 'PLAYER_ID': 203186}, {'NBA_FANTASY_PTS': 10.4, 'PLAYER_NAME': 'Sam Dekker', 'PLAYER_ID': 1626155}, {'NBA_FANTASY_PTS': 8.2, 'PLAYER_NAME': 'Sindarius Thornwell', 'PLAYER_ID': 1628414}, {'NBA_FANTASY_PTS': 5.9, 'PLAYER_NAME': 'Brice Johnson', 'PLAYER_ID': 1627744}],
1610612750: [{'NBA_FANTASY_PTS': 43.1, 'PLAYER_NAME': 'Karl-Anthony Towns', 'PLAYER_ID': 1626157}, {'NBA_FANTASY_PTS': 41.0, 'PLAYER_NAME': 'Jimmy Butler', 'PLAYER_ID': 202710}, {'NBA_FANTASY_PTS': 30.4, 'PLAYER_NAME': 'Jeff Teague', 'PLAYER_ID': 201952}, {'NBA_FANTASY_PTS': 29.7, 'PLAYER_NAME': 'Andrew Wiggins', 'PLAYER_ID': 203952}, {'NBA_FANTASY_PTS': 26.8, 'PLAYER_NAME': 'Taj Gibson', 'PLAYER_ID': 201959}, {'NBA_FANTASY_PTS': 16.3, 'PLAYER_NAME': 'Gorgui Dieng', 'PLAYER_ID': 203476}, {'NBA_FANTASY_PTS': 15.2, 'PLAYER_NAME': 'Jamal Crawford', 'PLAYER_ID': 2037}, {'NBA_FANTASY_PTS': 14.2, 'PLAYER_NAME': 'Tyus Jones', 'PLAYER_ID': 1626145}, {'NBA_FANTASY_PTS': 11.3, 'PLAYER_NAME': 'Nemanja Bjelica', 'PLAYER_ID': 202357}, {'NBA_FANTASY_PTS': 6.7, 'PLAYER_NAME': 'Shabazz Muhammad','PLAYER_ID': 203498}, {'NBA_FANTASY_PTS': 4.5, 'PLAYER_NAME': 'Aaron Brooks', 'PLAYER_ID': 201166}, {'NBA_FANTASY_PTS': 2.7, 'PLAYER_NAME': 'Marcus Georges-Hunt', 'PLAYER_ID': 1627875}, {'NBA_FANTASY_PTS': 1.8, 'PLAYER_NAME': 'Cole Aldrich', 'PLAYER_ID': 202332}],
1610612761: [{'NBA_FANTASY_PTS': 39.6, 'PLAYER_NAME': 'DeMar DeRozan', 'PLAYER_ID': 201942}, {'NBA_FANTASY_PTS': 35.7, 'PLAYER_NAME': 'Kyle Lowry', 'PLAYER_ID': 200768}, {'NBA_FANTASY_PTS': 25.8, 'PLAYER_NAME': 'Serge Ibaka', 'PLAYER_ID': 201586}, {'NBA_FANTASY_PTS': 23.2, 'PLAYER_NAME': 'Jonas Valanciunas', 'PLAYER_ID': 202685}, {'NBA_FANTASY_PTS': 20.3, 'PLAYER_NAME': 'Delon Wright', 'PLAYER_ID':1626153}, {'NBA_FANTASY_PTS': 18.0, 'PLAYER_NAME': 'Pascal Siakam', 'PLAYER_ID': 1627783}, {'NBA_FANTASY_PTS': 16.6, 'PLAYER_NAME': 'Jakob Poeltl', 'PLAYER_ID': 1627751}, {'NBA_FANTASY_PTS': 15.8, 'PLAYER_NAME': 'CJ Miles', 'PLAYER_ID': 101139}, {'NBA_FANTASY_PTS': 15.7, 'PLAYER_NAME': 'Fred VanVleet', 'PLAYER_ID': 1627832}, {'NBA_FANTASY_PTS': 13.1, 'PLAYER_NAME': 'Norman Powell', 'PLAYER_ID': 1626181}, {'NBA_FANTASY_PTS': 12.5, 'PLAYER_NAME': 'OG Anunoby', 'PLAYER_ID': 1628384}, {'NBA_FANTASY_PTS': 11.1, 'PLAYER_NAME': 'Lucas Nogueira', 'PLAYER_ID': 203512}, {'NBA_FANTASY_PTS': 4.6, 'PLAYER_NAME': 'Lorenzo Brown', 'PLAYER_ID': 203485}, {'NBA_FANTASY_PTS': 2.9, 'PLAYER_NAME': 'Bruno Caboclo', 'PLAYER_ID': 203998}, {'NBA_FANTASY_PTS': 2.8, 'PLAYER_NAME': 'Malcolm Miller', 'PLAYER_ID': 1626259}, {'NBA_FANTASY_PTS': 2.6, 'PLAYER_NAME': 'Alfonzo McKinnie', 'PLAYER_ID': 1628035}],
1610612737: [{'NBA_FANTASY_PTS': 34.6, 'PLAYER_NAME': 'Dennis Schroder', 'PLAYER_ID': 203471}, {'NBA_FANTASY_PTS': 28.0, 'PLAYER_NAME': 'Kent Bazemore', 'PLAYER_ID': 203145}, {'NBA_FANTASY_PTS': 24.9, 'PLAYER_NAME': 'Taurean Prince', 'PLAYER_ID': 1627752}, {'NBA_FANTASY_PTS': 24.4, 'PLAYER_NAME': 'John Collins', 'PLAYER_ID': 1628381}, {'NBA_FANTASY_PTS': 24.3, 'PLAYER_NAME': 'Dewayne Dedmon', 'PLAYER_ID': 203473}, {'NBA_FANTASY_PTS': 22.8, 'PLAYER_NAME': 'Ersan Ilyasova', 'PLAYER_ID': 101141}, {'NBA_FANTASY_PTS': 18.8, 'PLAYER_NAME': 'Marco Belinelli', 'PLAYER_ID': 201158}, {'NBA_FANTASY_PTS': 13.5, 'PLAYER_NAME': 'Malcolm Delaney', 'PLAYER_ID': 1627098}, {'NBA_FANTASY_PTS': 13.1, 'PLAYER_NAME': 'Mike Muscala', 'PLAYER_ID': 203488}, {'NBA_FANTASY_PTS': 12.3, 'PLAYER_NAME': 'Miles Plumlee', 'PLAYER_ID': 203101}, {'NBA_FANTASY_PTS': 11.2, 'PLAYER_NAME': "DeAndre' Bembry", 'PLAYER_ID': 1627761}, {'NBA_FANTASY_PTS': 11.0, 'PLAYER_NAME': 'Tyler Cavanaugh', 'PLAYER_ID': 1628463}, {'NBA_FANTASY_PTS': 10.9, 'PLAYER_NAME': 'Luke Babbitt', 'PLAYER_ID': 202337}, {'NBA_FANTASY_PTS': 10.6, 'PLAYER_NAME': 'Isaiah Taylor', 'PLAYER_ID': 1627819}, {'NBA_FANTASY_PTS': 6.6, 'PLAYER_NAME': 'Josh Magette', 'PLAYER_ID': 203705}, {'NBA_FANTASY_PTS': 5.4, 'PLAYER_NAME': 'Tyler Dorsey', 'PLAYER_ID': 1628416}, {'NBA_FANTASY_PTS': 0.9, 'PLAYER_NAME': 'Nicolas Brussino', 'PLAYER_ID': 1627852}]
}


def get_starters_by_team(soup):
    """
    Returns a dictionary from team abbreviations to
    a list of player names who are starting today.

    soup: BeautifulSoup scraped from ROTOWIRE_URL.
    """
    game_divs = soup.find_all('div', class_='offset1 span15')

    starters_by_abbreviation = {}
    for game_div in game_divs:
        game_header = game_div.find_all(
            'div', class_='span15 dlineups-topbox')[0]
        team_name_1 = game_header.find_all(
            'div', class_='span5 dlineups-topboxleft')[0].text.strip()
        team_name_2 = game_header.find_all(
            'div', class_='span5 dlineups-topboxright')[0].text.strip()

        # convert to nba abbreviations (Ex. PHX instead of PHO)
        team_name_1 = map_team_abbrevs(team_name_1)
        team_name_2 = map_team_abbrevs(team_name_2)

        players_div = game_div.find_all(
            'div', class_='span15 dlineups-mainbox')[0]

        # find starters
        team_lineup_divs = players_div.find_all('div', recursive=False)[
            1].find_all('div', class_='dlineups-half')
        for team_name, lineup_div in zip((team_name_1, team_name_2), team_lineup_divs):
            starter_names = [match_name(player_a['title'].strip())
                             for player_a in lineup_div.find_all('a')]
            starters_by_abbreviation[team_name] = starter_names

    return starters_by_abbreviation

def get_injured_by_team(soup):
    """
    Returns a dictionary from team abbreviations to
    a list of player names who are injured today.

    soup: BeautifulSoup scraped from ROTOWIRE_URL.
    """
    game_divs = soup.find_all('div', class_='offset1 span15')

    injured_by_abbreviation = {}
    for game_div in game_divs:
        game_header = game_div.find_all(
            'div', class_='span15 dlineups-topbox')[0]
        team_name_1 = game_header.find_all(
            'div', class_='span5 dlineups-topboxleft')[0].text.strip()
        team_name_2 = game_header.find_all(
            'div', class_='span5 dlineups-topboxright')[0].text.strip()
        
        # convert to nba abbreviations (Ex. PHX instead of PHO)
        team_name_1 = map_team_abbrevs(team_name_1)
        team_name_2 = map_team_abbrevs(team_name_2)

        players_div = game_div.find_all(
            'div', class_='span15 dlineups-mainbox')[0]

        # find injured
        team_lineup_divs = players_div.find_all('div', recursive=False)[
            2].find_all('div', class_='dlineups-half equalheight')
        for team_name, lineup_div in zip((team_name_1, team_name_2), team_lineup_divs):
            injured_names = [match_name(player_a.text.strip())
                             for player_a in lineup_div.find_all('a')]
            injured_by_abbreviation[team_name] = set(injured_names)

    return injured_by_abbreviation

def get_matchups(soup):
    """
    Returns a list of matchups.
    A matchup is a tuple of two team abbreviations.
    The game is located at the second team's home.

    soup: BeautifulSoup scraped from ROTOWIRE_URL.
    """
    game_divs = soup.find_all('div', class_='offset1 span15')

    matchups = []
    for game_div in game_divs:
        game_header = game_div.find_all(
            'div', class_='span15 dlineups-topbox')[0]
        team_name_1 = game_header.find_all(
            'div', class_='span5 dlineups-topboxleft')[0].text.strip()
        team_name_2 = game_header.find_all(
            'div', class_='span5 dlineups-topboxright')[0].text.strip()
        
        # convert to nba abbreviations (Ex. PHX instead of PHO)
        team_name_1 = map_team_abbrevs(team_name_1)
        team_name_2 = map_team_abbrevs(team_name_2)
        
        matchups.append((team_name_1, team_name_2))

    return matchups


def get_nba_lineup(team_id):
    """
    Given a team_id, scrapes from the official NBA website the
    team's roster corresponding to the team_id.
    """
    if team_id in NBA_LINEUPS_SNAPSHOT:
        return NBA_LINEUPS_SNAPSHOT[team_id]

    api_request = NBA_LINEUP_URL.format(
        **{'team_id': team_id, 'season': app.config['CURRENT_SEASON']})
    response = requests.get(url=api_request,
                            headers={'User-agent': USER_AGENT},
                            stream=True,
                            allow_redirects=False).json()['resultSets'][RESULT_SET_INDEX]
    headers = response['headers']
    rows = response['rowSet']
    chosen_columns = ('PLAYER_ID', 'PLAYER_NAME', 'NBA_FANTASY_PTS')
    chosen_indicies = tuple(headers.index(col) for col in chosen_columns)
    

    lineup = [{col: row[index] for col, index in zip(chosen_columns, chosen_indicies)} for row in rows]
    sorted_lineups = sorted(lineup, key=lambda d: -d['NBA_FANTASY_PTS'])
    print (team_id)
    print(sorted_lineups)
    return sorted_lineups


def get_game_day_lineup(team_abbrev, team_id, starter_names, injured_names):
    """
    Returns a lineup for a given team (proper json response).
    """
    nba_lineup = get_nba_lineup(team_id)

    game_day_lineup = []
    for player in nba_lineup:
        player_name = player['PLAYER_NAME']
        player_id = player['PLAYER_ID']
        starter_index = starter_names.index(player_name) if player_name in starter_names else -1
        position = POSITIONS_ORDER[starter_index] if starter_index != -1 else ''
        is_injured = player_name in injured_names
        game_day_lineup.append({
            'name': player_name,
            'playerId': player_id,
            'team': team_abbrev,
            'position': position,
            'isInjured': is_injured
        })
    
    return game_day_lineup


@app.route('/lineups', methods=['GET'])
def lineups_endpoint():
    """
    Returns all lineups for today in json format
    specified in the json schema.
    """
    team_abbrev_to_team_id_map = get_team_abbrev_team_id_map()
    soup = BeautifulSoup(requests.get(ROTOWIRE_URL).content, 'html.parser')
    starters_by_abbrev = get_starters_by_team(soup)
    injured_by_abbrev = get_injured_by_team(soup)
    matchups = get_matchups(soup)

    lineups = {}
    for team_abbrev in starters_by_abbrev:
        team_id = team_abbrev_to_team_id_map[team_abbrev]
        lineup = get_game_day_lineup(
            team_abbrev, team_id, starters_by_abbrev[team_abbrev], injured_by_abbrev[team_abbrev])
        lineups[team_abbrev] = lineup

    resp = {}
    resp['lineups'] = lineups
    resp['matchups'] = matchups
    return json.dumps(resp)
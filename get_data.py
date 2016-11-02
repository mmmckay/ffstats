from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
import time
import os
import pandas as pd
import numpy as np
import math
import sys

base_dir = os.getcwd()
owner_dict = { 1:'Strangeway',
				2:'Fisher',
				3:'Wang',
				4:'Ng',
				7:'Gupta',
				8:'Sitek',
				9:'Kay',
				10:'Cook',
				12:'Gallerani',
				13:'May',
				14:'Adams',
				15:'Dornbrook'}

username = input('\nESPN email:  ')
password = input('\nPassword:  ')

def webdriver_login():
	#load selenium driver to access html pages through phontomjs
	driver = webdriver.PhantomJS(base_dir + '/phantomjs_mac')
	driver.get('http://espn.go.com/login')
	time.sleep(3)
	driver.switch_to.frame('disneyid-iframe')

	#Login to ESPN
	text_area = driver.find_element_by_xpath('//*[@id="did-ui"]/div/div/section/section/form/section/div[1]/div/label/span[2]/input')
	pass_area = driver.find_element_by_xpath('//*[@id="did-ui"]/div/div/section/section/form/section/div[2]/div/label/span[2]/input')
	text_area.send_keys(username)
	pass_area.send_keys(password)
	login_btn = driver.find_element_by_xpath('//*[@id="did-ui"]/div/div/section/section/form/section/div[3]/button')
	login_btn.click()

	time.sleep(5)

	print('Logged in')

	return driver

def create_directories(driver):
	os.mkdir('ffdata')
	os.chdir('ffdata')

	#create schedule file
	schedule_url = 'http://games.espn.com/ffl/schedule?leagueId=433483' 
	driver.get(schedule_url)
	html = driver.page_source
	soup = BeautifulSoup(html, "html.parser")
	matchups = soup.findAll('table', {'bgcolor':'#ffffff'})
	rows = matchups[0].findAll('td')
	schedule = {}
	current_week = 0
	week_schedule = []
	for row in rows:
		if row.a:
			if row.a.has_attr('name'):
				schedule[int(current_week)] = week_schedule
				current_week = row.a['name'].split('matchup')[1]
				week_schedule = []
			if row.a.has_attr('href') and 'PeriodId' not in row.a['href']:
				week_schedule.append(int(row.a['href'].split('teamId=')[1].split('&')[0]))
	for key in schedule:
		paired = []
		for n, user in enumerate(schedule[key]):
			if n%2 == 0:
				tup = (user,)
			else:
				paired.append(tup + (user,))
		schedule[key] = paired

	schedule_df = pd.DataFrame(index=owner_dict.keys(), columns=[key for key in schedule.keys() if schedule[key]])

	for key in schedule:
		if schedule[key]:
			for pair in schedule[key]:
				schedule_df.ix[pair[0],key] = pair[1]
				schedule_df.ix[pair[1],key] = pair[0]

	schedule_df = schedule_df.sort_index().sort_index(axis=1)

	schedule_df.to_csv('schedule.csv')

	overall_df = pd.DataFrame(index = owner_dict.keys(), columns = ['owner name', 'wins', 'losses', 'total points', 'total projected', 'avg points', 'avg projected', 'total against', 'avg against', 'median points', 'std_dev', 'std_err'])

	overall_df.to_csv('overall.csv')

	blank_owner_df = pd.DataFrame(columns=['points', 'projected', 'bench points', 'bench projected', 'top scorer', 'top bench scorer', 'double digits', 'zeroes', 'opponent', 'opponent score', 'opponent projected', 'line', 'over/under', 'favorite', 'win'])
	
	for owner_id in owner_dict:
		blank_owner_df.to_csv('{}_{}_overall.csv'.format(owner_id, owner_dict[owner_id]))

	os.chdir(base_dir)

def scrape_html(driver, collection_week):
	os.chdir(base_dir + '/ffdata')
	schedule_df = pd.read_csv('schedule.csv', index_col=0)
	week_overall = {}
	print('Week {}'.format(collection_week))
	if not os.path.exists('week{}'.format(collection_week)):
		os.mkdir('week{}'.format(collection_week))
	os.chdir('week{}'.format(collection_week))

	week_df = pd.DataFrame(columns=['points', 'projected', 'bench points', 'bench projected', 'top scorer', 'top bench scorer', 'double digits', 'zeroes', 'opponent', 'opponent score', 'opponent projected', 'line', 'over/under', 'favorite', 'win'])

	for owner_id in owner_dict:
		print('parsing html for {}'.format(owner_dict[owner_id]))
		teampage_url = 'http://games.espn.com/ffl/clubhouse?leagueId=433483&teamId={}&scoringPeriodId={}'.format(owner_id, collection_week)
		matchup_url = 'http://games.espn.com/ffl/boxscorequick?leagueId=433483&teamId={}&scoringPeriodId={}&seasonId=2016&view=scoringperiod&version=quick'.format(owner_id, collection_week)

		#get projections
		driver.get(teampage_url)
		html =  driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		tds = soup.findAll('td', {'class':'playertableStat appliedPoints'})
		ids = [4*n+3 for n in range(18)] 
		projected = [score.get_text() for n, score in enumerate(tds) if n in ids and score.get_text() != 'PROJ']
		
		#get team info
		columns = ['slot', 'player', 'position', 'points', 'projected']
		team_df = pd.DataFrame(columns=columns)
		driver.get(matchup_url)
		html = driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		slot = soup.findAll('td', {'class':'playerSlot'})
		name = soup.findAll('td', {'class':'playertablePlayerName'})
		points = [score.get_text() for score in soup.findAll('td', {'class':'appliedPoints'}) if score.get_text() != 'PTS']
		for n in range(16):
			player = name[n].get_text().split(',')
			if len(player) > 1:
				player_name = player[0].replace('*', '')
				player_position = player[1].replace(' ','').split('\xa0')[1]
			else:
				player_name = player[0].split('\xa0')[0].replace('*','')
				player_position = player[0].split('\xa0')[1]

			team_df.loc[n] = [slot[n].get_text(), player_name, player_position, points[n], projected[n]]

		total_points = sum([float(score) for score in team_df[team_df['slot'] != 'Bench']['points'] if score != '--'])
		projected = sum([float(score) for score in team_df[team_df['slot'] != 'Bench']['projected'] if score != '--'])
		bench_points = sum([float(score) for score in team_df[team_df['slot'] == 'Bench']['points'] if score != '--'])
		bench_projected = sum([float(score) for score in team_df[team_df['slot'] == 'Bench']['projected'] if score != '--'])
		top_scorer = max(team_df[team_df['slot'] != 'Bench']['points'])
		top_bench = max(team_df[team_df['slot'] == 'Bench']['points'])
		double_digits = len([n for n in team_df[team_df['slot'] != 'Bench']['points'] if n != '--' and float(n) >= 10])
		zeroes = len([n for n in team_df[team_df['slot'] != 'Bench']['points'] if n != '--' and float(n) <= 0])

		week_overall[owner_id] = [total_points, projected, bench_points, bench_projected, top_scorer, top_bench, double_digits, zeroes]
		team_df.to_csv('{}_{}_playerscores'.format(owner_id, owner_dict[owner_id]))

	#extra stats
	print('crunching the numbers..')
	for owner_id in owner_dict:
		opponent = int(schedule_df.ix[owner_id, collection_week-1])
		opp_score = week_overall[opponent][0]
		opp_proj = week_overall[opponent][1]
		line = week_overall[owner_id][1] - opp_proj
		over_under = week_overall[owner_id][1] + opp_proj
		if line < 0:
			favorite = True
		else:
			favorite = False
		if week_overall[owner_id][0] > opp_score:
			win = True
		else:
			win = False

		week_overall[owner_id].extend((opponent, opp_score, opp_proj, line, over_under, favorite, win))

		week_df.loc[owner_id] = week_overall[owner_id]
		week_df.to_csv('owner_scores_week_{}.csv'.format(collection_week))

	os.chdir('../')

	overall_df = pd.read_csv('overall.csv', index_col=0)

	for owner_id in owner_dict:
		filename = '{}_{}_overall.csv'.format(owner_id, owner_dict[owner_id])
		owner_df = pd.read_csv(filename, index_col=0)
		owner_df.loc[collection_week] = week_overall[owner_id]
		#overall recalculation
		scores = [float(n) for n in owner_df['points']]
		proj = [float(n) for n in owner_df['projected']]
		opp_scores = [float(n) for n in owner_df['opponent score']]
		wins = len(owner_df[owner_df['win'] == True]['win'].tolist())
		losses = len(owner_df[owner_df['win'] == False]['win'].tolist())  
		total_points = sum(scores)
		total_proj = sum(proj)
		opp_total = sum(opp_scores)
		opp_avg = np.mean(opp_scores)
		avg_points = np.mean(scores)
		avg_proj = np.mean(proj)
		median = np.median(scores)
		std_dev = np.std(scores)
		std_err = std_dev/math.sqrt(len(scores))

		overall_df.loc[owner_id] = [owner_dict[owner_id], wins, losses, total_points, total_proj, avg_points, avg_proj, opp_total, opp_avg, median, std_dev, std_err]

		owner_df.to_csv(filename)

	overall_df.to_csv('overall.csv')

def main(collect_week, all_weeks=False):
	driver = webdriver_login()
	
	if not os.path.exists('ffdata'):
		create_directories(driver)

	if all_weeks:
		for week in range(1, int(collect_week) + 1):
			scrape_html(driver, week)
	else:
		scrape_html(driver, int(collect_week))

	driver.quit()
	exit()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		exit('No week specified for scraping, exiting')
	if len(sys.argv) == 2:
		print('Getting fanatsy data for week {}'.format(sys.argv[1]))
		main(sys.argv[1])
	if len(sys.argv) == 3:
		if sys.argv[2] == '--all':
			print('Getting fantasy data from the beginning to week {}'.format(sys.argv[1]))
			main(sys.argv[1], True)




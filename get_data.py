from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
import time
import os
import pandas as pd

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

def webdriver_login():
	#load selenium driver to access html pages through chrome
	chromedriver = base_dir + '/chromedriver64'
	driver = webdriver.Chrome(chromedriver)
	driver.get('http://espn.go.com/login')
	time.sleep(3)
	driver.switch_to.frame('disneyid-iframe')

	#Login to ESPN
	text_area = driver.find_element_by_xpath('//*[@id="did-ui"]/div/div/section/section/form/section/div[1]/div/label/span[2]/input')
	pass_area = driver.find_element_by_xpath('//*[@id="did-ui"]/div/div/section/section/form/section/div[2]/div/label/span[2]/input')
	text_area.send_keys("matthewckay@gmail.com")
	pass_area.send_keys('3EDCvgy7uespn')
	login_btn = driver.find_element_by_xpath('//*[@id="did-ui"]/div/div/section/section/form/section/div[3]/button')
	login_btn.click()

	time.sleep(5)

	return driver

def create_directories(driver):
	if not os.path.exists('ffdata'):
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

	schedule_df = pd.DataFrame(index=player_dict.keys(), columns=[key for key in schedule.keys() if schedule[key]])

	for key in schedule:
		if schedule[key]:
			for pair in schedule[key]:
				schedule_df.ix[pair[0],key] = pair[1]
				schedule_df.ix[pair[1],key] = pair[0]

	schedule_df = schedule_df.sort_index().sort_index(axis=1)

	schedule_df.to_csv('schedule.csv')

	players_df = pd.DataFrame(columns=['total points', 'avg', 'projected avg', 'best week', 'weeks started', 'weeks owned'])

	players_df.to_csv('players.csv')

def scrape_html(driver, collection_week):
	os.chdir('ffdata')
	owner_df = pd.DataFrame(columns=['points', 'projected', 'bench points', 'bench_projected', 'top scorer', 'top bench scorer', 'double digits', 'zeroes'])
	players_df = pd.read_csv('players.csv',index_col=0)

	for owner_id in owner_dict:
		teampage_url = 'http://games.espn.com/ffl/clubhouse?leagueId=433483&teamId={}&scoringPeriodId={}'.format(owner_id, collection_week)
		matchup_url = 'http://games.espn.com/ffl/boxscorequick?leagueId=433483&teamId={}&scoringPeriodId={}&seasonId=2016&view=scoringperiod&version=quick'.format(owner_id, collection_week)

		#get projections
		driver.get(teampage_url)
		html =  driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		tds = soup.findAll('td', {'class':'playertableStat appliedPoints'})
		ids = [4*n+3 for n in range(18)] 
		projected = [float(score.get_text()) for n, score in enumerate(tds) if n in ids and score.get_text() != 'PROJ']
		
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
		double_digits = len([n for n in team_df[team_df['slot'] != 'Bench']['points'] if n >= 10])
		zeroes = len([n for n in team_df[team_df['slot'] != 'Bench']['points'] if n <= 0])

		owner_df.loc[owner_id] = [total_points, projected, bench_points, bench_projected, top_scorer, top_bench, double_digits, zeroes]
		print(team_df)

	print(owner_df)
	driver.quit()
	exit()

driver = webdriver_login()
#create_directories(driver)
scrape_html(driver, 7)

os.chdir('ffdata')
players_df = pd.read_csv('players.csv',index_col=0)
print(players_df)

players_df.loc['Aaron Rodgers'] = [10, 10, 10, 10, 10, 10]

if 'Aaron Rodgers' in players_df.index:
	print('yes')



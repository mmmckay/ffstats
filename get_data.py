from selenium import webdriver
from bs4 import BeautifulSoup, SoupStrainer
import time

def webdriver_login():
	#load selenium driver to access html pages through chrome
	chromedriver = '/Users/matthewckay/projects/ff/chromedriver64'
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

def scrape_html(driver, current_week, collection_week=None):
	player_dict = { 1:'Strangeway',
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

	for player_id in player_dict:
		teampage_url = 'http://games.espn.com/ffl/clubhouse?leagueId=433483&teamId={}&seasonId=2016'.format(player_id)
		matchup_url = 'http://games.espn.com/ffl/boxscorequick?leagueId=433483&teamId={}&scoringPeriodId={}&seasonId=2016&view=scoringperiod&version=quick'.format(player_id, collection_week)
		opponents_url = 'http://games.espn.com/ffl/scoreboard?leagueId=433483&matchupPeriodId={}'.format(collection_week)
		
		#get matchup info
		driver.get(matchup_url)
		html = driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		position = soup.findAll('td', {'class':'playerSlot'})
		name = soup.findAll('td', {'class':'playertablePlayerName'})
		points = soup.findAll('td', {'class':'appliedPoints'})
		for n in range(16):
			print(position[n].get_text(), name[n].get_text(), points[n+1].get_text())

		#get opponents info
		driver.get(opponents_url)
		html = driver.page_source
		soup = BeautifulSoup(html, "html.parser")
		userid_matchups = soup.findAll('a', {'target':'_top'})
		matchups = []
		for n, userid_html in enumerate(userid_matchups):
			if n != 0:
				if n%2 == 0:
					matchups.append(tup + (userid_html['href'].split('teamId=')[1].split('&')[0],))
				else:
					tup = (userid_html['href'].split('teamId=')[1].split('&')[0],)

		print(matchups)
		driver.quit()
		exit()

driver = webdriver_login()
scrape_html(driver, 7, 1)

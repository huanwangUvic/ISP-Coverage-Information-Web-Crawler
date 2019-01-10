from bs4 import BeautifulSoup as bs
import requests
import re
import mysql.connector

commitCount = 0
global db
tar_state = 'or' # could be any state of the US, 'or' for oregon

def getISPId(tdispIdString):
	pattern = '<td><a href="https://geoisp.com/provider/(\d+?)/">'
	matcher = re.search(pattern, tdispIdString)
	return matcher.group(1)
	
def getPercent(tdPercentString):
	pattern = '<td>(.+?)</td>'
	matcher = re.search(pattern, tdPercentString)
	return matcher.group(1)

def getCountyNameByURLTail(URLTail):
	pattern = '/wiki/(.+?)_County,_'
	matcher = re.search(pattern, URLTail)
	return matcher.group(1).replace('_', ' ')

def getCityListByState(stateName):
	'''This function recv stateName (WA, OR, CA) as args, and return a dictionary with county as key, 
	and the corresponding list of cities as value.'''
	stateName = stateName.lower()
	stateWikiURL = ''
	if stateName not in ['wa', 'or', 'ca']:
		print('Wrong args')
		return
	cityDict = {}
	countyPopuDict = {}
	stateWikiURL = 'https://en.wikipedia.org/wiki/List_of_counties_in_'
	if stateName == 'wa':
		stateWikiURL = stateWikiURL + 'Washington'
	elif stateName =='or':
		stateWikiURL = stateWikiURL + 'Oregon'
	else:
		stateWikiURL = stateWikiURL + 'California'
	
	html = requests.get(stateWikiURL).text
	if html is None:
		return False
	
	soup = bs(html, 'html.parser')
	
	#############################################
	table = soup.find('table', class_= 'wikitable sortable')
	countTr = 0
	for tr in table.contents:
		if tr.name != 'tr':
			continue
		if countTr == 0: # first tr contains the table title infomation
			countTr += 1
			continue
		if tr.contents is None:
			print('report this error, tr contents is None')
			continue
		countTd = 0
		for td in tr.contents:
			if td.name != 'td':
				continue
			if countTd == 0:
				couty_name = td.string.replace(' County', '')
			countTd += 1
			if countTd == 7: # population info is in the 7th column of table
				if td.contents[0].name == 'span':
					population = td.contents[1].replace(',', '')
				else:
					population = 0
					print('Report this error, no span here')
				break
		countyPopuDict[couty_name] = int(population)
		
	##################################################
	
	tags = soup.find_all("div", style = re.compile('position:absolute;.+'))
	for county in tags:
		countySuf = county.contents[0]['href']
		cityList = getCityListByCounty(countySuf)
		countyName = getCountyNameByURLTail(countySuf)
		
		cityDict[countyName] = cityList
		
	return cityDict, countyPopuDict

def getCityListByCounty(countySuffix): # e.g., "King_County,_Washington"
	baseURL = "https://en.wikipedia.org"
	html = requests.get(baseURL + countySuffix).text
	soup = bs(html, "html.parser")
	# print (soup.prettify())
	tag = soup.find('span', attrs={'id':['Cities', 'City', 'Incorporated_cities']})
	if tag is None:
		print('No tags got for county {0}'.format(countySuffix))
		return []
	cityTagList = []
	for sibling in tag.parent.next_siblings:
		if sibling.name == 'ul':
			cityTagList = sibling.contents
			break
		elif sibling.name == 'div':
			if sibling['class'] == ['thumb', 'tright']:
				continue
			for child in sibling.children:
				if child.name == 'ul':
					cityTagList = child.contents 
					break
			break
		
	cityList = []
	for tag in cityTagList:
		if tag.name == 'li':
			cityList.append(tag.contents[0].string)
			
	return cityList

##################################################################

def getIspCovInfo(cityName, stateName): #e.g., chelan, WA
	if cityName is None or stateName is None:
		print('Wrong input arguments')
		return -1
	cityName = cityName.lower().replace(' ', '-')
	cityName = cityName.replace('st.-', 'saint-').replace('mt.-', 'mount-')
	
	geoipBaseUrl = 'https://geoisp.com/us/'
	html = requests.get(geoipBaseUrl + stateName + '/' + cityName + '/').text
	if html is None:
		print('No ISP information for city {0} in {1}'.format(cityName, stateName))

		return -1
		
	dslIspInfo, cableIspInfo = [], []
	soup = bs(html, 'html.parser')
	# print (soup.prettify())
	ispTextList = ['DSL Providers', 'Cable Providers']
	for indx, textisp in enumerate(ispTextList):
		tag = soup.find('tr', text=textisp)
		if tag is None:
			print('No {0} info for {1}'.format(textisp, cityName))
			continue
		for sibling in tag.next_siblings:
			if sibling is None:
				break
			if sibling.name != 'tr':
				print('abnormal')
				break
			if 'bgcolor' in sibling.attrs or (sibling.string is not None and 'Fiber' in sibling.string):
				break # checking cable providers done
			if 'class' not in sibling.attrs:
				break
			ispId, percent = 0, 0.0
			for td in sibling.contents:
				td = str(td)
				if '<td>' not in td:
					continue
				if ispId == 0:
					ispId = getISPId(td)
					continue
				if percent == 0.0:
					percent = getPercent(td)
					break
			if ispId != 0:
				if 0 == indx:
					dslIspInfo.append([ispId, percent])
				else:
					cableIspInfo.append([ispId, percent])
	
	return [dslIspInfo, cableIspInfo]
	
##################################################################

def getISPNameById(ispId): #e.g., chelan, WA
	baseURL = 'https://geoisp.com/provider/' + str(ispId)
	html = requests.get(baseURL).text
	if html is None:
		return ""
	soup = bs(html, 'html.parser')
	titleString = soup.title.string
	pattern = '(.+) - Reviews and Coverage Map - geoISP'
	matcher = re.search(pattern, titleString)
	if matcher is None:
		return ""
		
	return matcher.group(1)
	
##################################################################

def insertRecToTables(tableIndx, varList, cursor):
	global commitCount
	global db
	
	if tableIndx == 0:
		sql = """INSERT INTO city (cityName, countyId, stateId, cityPopu)\
                 VALUES ('{0}', {1}, {2}, {3})""".format(varList[0], varList[1], varList[2], varList[3])
	elif tableIndx == 1:
		sql = """INSERT INTO county (countyName, stateId, countyPopu)\
              VALUES ('{0}', {1}, {2})""".format(varList[0], varList[1], varList[2])
	elif tableIndx == 2:
		sql = """INSERT INTO covrecord (ispId, covRatio, ispType, cityId)\
              VALUES ({0}, {1}, {2}, {3})""".format(varList[0], varList[1], varList[2], varList[3])
	else:
		sql = """INSERT INTO ispinfo (ispId, ispName)\
               VALUES ({0}, '{1}')""".format(varList[0], varList[1])
		
	try:
		cursor.execute(sql)
		commitCount += 1
		if commitCount == 100:
			db.commit()
			commitCount = 0
	except:
		db.rollback()

##################################################################

def validPopulationThTag(tag):
  return (tag.name == 'th') and ('Population' in tag.text)

def getCityPopuByName(cityName, stateName):
	population = 0
	
	if (stateName == 'wa'):
		stateName = 'Washington'
	elif stateName == 'or':
		stateName = 'Oregon'
	elif stateName == 'ca':
		stateName = 'California'
	else:
		print('Wrong state info')
		return 0
	baseURL = 'https://en.wikipedia.org/wiki/'
	cityName = cityName.replace(' ', '_')
	baseURL = baseURL + cityName + ',_' + stateName
	
	html = requests.get(baseURL).text
	if html is None:
		return 0
	soup = bs(html, 'html.parser')
	tag = soup.find(validPopulationThTag)
	if tag is None:
		print('Cant find expected population tag:', cityName)
		return 0
	for sibling in tag.parent.next_siblings:
		if sibling == '\n':
			continue
		if sibling.name != 'tr':
			continue
		if sibling.contents[1].name != 'th':
			continue
		if any(s in sibling.contents[1].text for s in ('Total', 'City')):
			population = sibling.contents[3].string.replace(',', '')
			break
	
	return int(population)
	
##################################################################
	
if __name__ == '__main__':
	
	if tar_state == 'wa':
		tar_state_id = 0 # 1, 2
	elif tar_state == 'or':
		tar_state_id = 1
	elif tar_state == 'ca':
		tar_state_id = 2
	
	cityListdict, countyPopuDict = getCityListByState(tar_state)
	
	db = mysql.connector.connect(host = 'localhost', user = 'root', password = '5212352123', database = 'openadresses')
	cursor = db.cursor()
	
	try:
		cursor.execute('SELECT MAX(cityId) FROM city')
		cityId = cursor.fetchone()[0]
		cursor.execute('SELECT MAX(countyId) FROM county')
		countyId = cursor.fetchone()[0]
	except:
		print('cursor execution wrong')
		
	if cityId is None:
		cityId = 0
	if countyId is None:
		countyId = 0
	
	for county, cityList in cityListdict.items():
		countyId += 1
		if county not in countyPopuDict:
			print('Error: unknown county')
			countyPopuDict[county] = 0
		insertRecToTables(1, [county, tar_state_id, countyPopuDict[county]], cursor)
		for city in cityList:
			cityId += 1
			cityPopu = getCityPopuByName(city, tar_state)
			insertRecToTables(0, [city, countyId, tar_state_id, cityPopu], cursor)
			# print(county, ':', city, getIspCovInfo(city, tar_state))
			list = getIspCovInfo(city, tar_state)
			for indx, item in enumerate(list):	#item could be dslIspInfo or cableIspInfo
				for record in item:
					ispId = int(record[0])
					coverRatio = float(record[1].strip("%")) / 100
					insertRecToTables(2, [ispId, coverRatio, indx, cityId], cursor)
					
	db.commit()
	sql = 'SELECT DISTINCT ispId FROM covrecord'
	try:
		cursor.execute(sql)
		results = cursor.fetchall()
	except:
		print('sql execution/fetchall error')
		
	for ispId in results:
		ispName = getISPNameById(ispId[0])
		insertRecToTables(3, [ispId[0], ispName], cursor)
	
	db.commit()
	
	db.close()
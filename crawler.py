import mysql.connector
import tools
global db
tar_state = 'wa' # could be any state of the US, 'or' for oregon

# ------------------------ arguments for mysql database
hostName = 'localhost'
sql_user = 'root'
sql_password = '5212352123'
sql_database = 'mytest'

##################################################################

def checkTableExists(dbcon, tablename):
    dbcur = dbcon.cursor()
    dbcur.execute("""
        SELECT COUNT(*)
        FROM information_schema.tables
        WHERE table_name = '{0}'
        """.format(tablename))
    if dbcur.fetchone()[0] == 2:
        dbcur.close()
        return True

    dbcur.close()
    return False
	
if __name__ == '__main__':
	
	if tar_state == 'wa':
		tar_state_id = 0 # 1, 2
	elif tar_state == 'or':
		tar_state_id = 1
	elif tar_state == 'ca':
		tar_state_id = 2
	
	
	
	db = mysql.connector.connect(host = hostName, user = sql_user, password = sql_password, database = sql_database)
	cursor = db.cursor()
	
	if not checkTableExists(db, 'county'):
		tools.createTables(cursor)
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
	
	cityListdict, countyPopuDict = tools.getCityListByState(tar_state) # return list of cities as well as list of county Populations of the target state
	
	for county, cityList in cityListdict.items():
		countyId += 1
		if county not in countyPopuDict:
			print('Error: unknown county')
			countyPopuDict[county] = 0
		tools.insertRecToTables(1, [county, tar_state_id, countyPopuDict[county]], cursor, db)
		for city in cityList:
			cityId += 1
			cityPopu = tools.getCityPopuByName(city, tar_state)
			tools.insertRecToTables(0, [city, countyId, tar_state_id, cityPopu], cursor, db)
			# print(county, ':', city, getIspCovInfo(city, tar_state))
			list = tools.getIspCovInfo(city, tar_state)
			for indx, item in enumerate(list):	#item could be dslIspInfo or cableIspInfo
				for record in item:
					ispId = int(record[0])
					coverRatio = float(record[1].strip("%")) / 100
					tools.insertRecToTables(2, [ispId, coverRatio, indx, cityId], cursor, db)
					
	db.commit()
	sql = 'SELECT DISTINCT ispId FROM covrecord'
	try:
		cursor.execute(sql)
		results = cursor.fetchall()
	except:
		print('sql execution/fetchall error')
		
	for ispId in results:
		ispName = tools.getISPNameById(ispId[0])
		tools.insertRecToTables(3, [ispId[0], ispName], cursor, db)
	
	db.commit()
	
	db.close()
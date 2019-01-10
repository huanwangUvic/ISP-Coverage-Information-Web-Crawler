from geopy import geocoders
def getCordinateByName(cityName, stateName):
	gn = geocoders.GeoNames(username="huanwanghuanwang")
	cityStr = cityName + ", " + stateName
	info = gn.geocode(cityStr + ', US', exactly_one=False, timeout = 12)
	
	stateStr = ', ' + stateName + ','
	for res in info:
		if stateStr in res[0]:
			break
	else:
		print('Error occured')
		return False
	
	co_tuple = res[1]
	if (not(42 < co_tuple[0] < 49.5)) or (not(-116 > co_tuple[1] > -124.5)):
		print(info)
	return co_tuple
	

if __name__ == "__main__":
	print(getCordinateByName('Prosser', 'WA'))
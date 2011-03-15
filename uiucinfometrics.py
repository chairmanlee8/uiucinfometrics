#-------------------------------------------------------------------------
# uiucinfometrics.py
#-------------------------------------------------------------------------
# Provides methods querying data from various UIUC websites.
#-------------------------------------------------------------------------

from BeautifulSoup import BeautifulSoup
import mechanize
import re
import datetime
import time
import urllib2
import httplib
import HTMLParser
import pdb

UIUC_COURSE_CATALOG_HOME_URL = "http://courses.illinois.edu/cis/index.html"
UIUC_COURSE_CATALOG_BASE_URL = "http://courses.illinois.edu/cis/<year>/<season>/catalog/index.html"
UIUC_COURSE_CATALOG_SUBJECT_URL = "http://courses.illinois.edu/cis/<year>/<season>/catalog/<subject>/index.html?skinId=2169"
UIUC_COURSE_SCHEDULE_COURSE_URL = "http://courses.illinois.edu/cis/<year>/<season>/schedule/<subject>/<course>.html?skinId=2169"
UIUC_PAGE_NOT_FOUND = "http://courses.illinois.edu/pageNotFound.html"

# Returns array of tuples representing valid semesters (semesters listed on the UIUC website).
# [(year, semester)]
def get_archive_semesters():
    baseUrl = UIUC_COURSE_CATALOG_HOME_URL
    
    br = mechanize.Browser()
    br.set_handle_robots(False)
    response = br.open(baseUrl)
    responseText = response.read()
    
    soup = BeautifulSoup(responseText)
    archiveOptions = soup.find('ul', id='navlist').find('select', id='selectClassSchedule').findAll('option')
	
    returnList = []
    
    for row in archiveOptions:
        res = re.match(r'http://courses.illinois.edu/cis/(?P<year>\w+)/(?P<season>\w+)/\w*', row['value'])
		
        if res is not None:
            returnList += [(int(res.group('year')), res.group('season').lower())]
			
    return returnList

# year: YYYY format
# season: "summer", "fall", or "spring"
# Returns array of tuples (subject code, subject full name)
def get_subjects(year, season):
	baseUrl = re.sub("<year>", str(year), UIUC_COURSE_CATALOG_BASE_URL)
	baseUrl = re.sub("<season>", season, baseUrl)
	
	br = mechanize.Browser()
	br.set_handle_robots(False)
	response = br.open(baseUrl)
	responseText = response.read()
	
	soup = BeautifulSoup(responseText)
	contentTree = soup.find(id="ws-cis")
	contentTreeRows = contentTree.findAll(attrs={'class': "ws-subject-row"})
	
	returnList = []
	
	pars = HTMLParser.HTMLParser()
	
	for row in contentTreeRows:
		courseNumber = row.find(attrs={'class': 'ws-course-number'}).string.strip()
		courseTitle = pars.unescape(row.find(attrs={'class': 'ws-course-title'}).a.string)
		returnList += [(courseNumber, courseTitle)]
		
	return returnList
	
# year: YYYY
# season: see above
# subject: 3/4 letter code, uppercase
# Returns a list of tuples (class number, class full name)
def get_subject_courses(year, season, subject):
	baseUrl = re.sub("<year>", str(year), UIUC_COURSE_CATALOG_SUBJECT_URL)
	baseUrl = re.sub("<season>", season, baseUrl)
	baseUrl = re.sub("<subject>", subject, baseUrl)
	
	br = mechanize.Browser()
	br.set_handle_robots(False)
	while 1:
		try:
			response = br.open(baseUrl)
			responseText = response.read()
			break
		except (urllib2.URLError, httplib.IncompleteRead):
			act = raw_input('Oops! Internet connection error, (r)etry or (a)bort? ')
			if act == "r":
				continue
			else:
				assert 0
	
	soup = BeautifulSoup(responseText)
	contentTree = soup.find(id="ws-cis")
	contentTreeRows = contentTree.find(attrs={'class': 'ws-list'}).findAll(attrs={'class': 'ws-row'})
	
	returnList = []
	
	pars = HTMLParser.HTMLParser()
	
	for row in contentTreeRows:
		courseNumber = int(re.match(r"(?P<subject>[A-Z]+)\s*(?P<number>[0-9]+)", row.find(attrs={'class': 'ws-course-number'}).string).group('number'))
		courseName = pars.unescape(row.find(attrs={'class': 'ws-course-title'}).a.string)

		returnList += [(courseNumber, courseName)]
	
	return returnList
	
# As above, with addition of...
# course : integer, course number
# Returns list of section tuples (CRN, type, section code, (timeStart, timeEnd), days, location, instructor, creditHours)
# Or, if course is not offered return None
def get_course_sections(year, season, subject, course):
	baseUrl = re.sub("<year>", str(year), UIUC_COURSE_SCHEDULE_COURSE_URL)
	baseUrl = re.sub("<season>", season, baseUrl)
	baseUrl = re.sub("<subject>", subject, baseUrl)
	baseUrl = re.sub("<course>", str(course), baseUrl)
	
	br = mechanize.Browser()
	br.set_handle_robots(False)
	
	while 1:
		try:
			response = br.open(baseUrl)
			
			if response.geturl() == UIUC_PAGE_NOT_FOUND:
				return None
				
			responseText = response.read()
			break
		except (urllib2.URLError, httplib.IncompleteRead):
			act = raw_input('Oops! Internet connection error, (r)etry or (a)bort? ')
			if act == "r":
				continue
			else:
				assert 0
	
	soup = BeautifulSoup(responseText)
	contentTree = soup.find(id="ws-cis")

	chours = float(re.search(r"(?P<hours>[0-9]+)\s*hours", str(contentTree.find('div', 'ws-credit'))).group('hours'))
	
	contentTreeRows = contentTree.find('table','ws-section-table').findAll(valign='top')
	
	returnList = []
	pars = HTMLParser.HTMLParser()
	
	for row in contentTreeRows:
		if row.find(attrs={'headers':'ws-crn'}) is None:
			continue
		
		try:
			ccrn = int(re.match(r"(?P<crn>[0-9]+)", pars.unescape(row.find(attrs={'headers':'ws-crn'}).string)).group('crn'))
			ctype = pars.unescape(row.find(attrs={'headers':'ws-type'}).string).strip()
			ccode = re.match(r'(?P<ccode>\w+)', pars.unescape(row.find(attrs={'headers':'ws-section'}).string)).group('ccode')
			ctimere = re.findall(r'([0-9]+:[0-9]+\s*\w+)', pars.unescape(row.find(attrs={'headers':'ws-time'}).string))
			assert len(ctimere) == 2
			ctimestart = time.strptime(ctimere[0], '%I:%M %p')
			ctimeend = time.strptime(ctimere[1], '%I:%M %p')
			cdays = re.match(r'(?P<cdays>\w+)', pars.unescape(row.find(attrs={'headers':'ws-days'}).string)).group('cdays')
			clocationre = re.findall(r'(\w+)', re.sub(r'<.*?>', '', re.sub(r'<br.*?>', ' ', pars.unescape(str(row.find(attrs={'headers':'ws-location'}))))))
			clocation = ' '.join(clocationre)
			cinstructor = pars.unescape(row.find(attrs={'headers':'ws-instructor'}).string).strip()
			
			returnList += [(ccrn, ctype, ccode, (ctimestart, ctimeend), cdays, clocation, cinstructor, chours)]
		except (AttributeError, AssertionError):
			continue
		
	return returnList
	
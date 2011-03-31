from pysqlite2 import dbapi2 as sqlite
from collections import defaultdict
import simplejson as json
import sys
import re

COURSE_TABLE_NAME = "uiuc_courses"
SECTION_TABLE_NAME = "uiuc_sections"
DATABASE_NAME = "/home/smiley325/projects/uiucinfometrics/uiuc_course_catalog.db"

# ---------------------------------------------------
# UIUC Catalog AJAX version
# ---------------------------------------------------

def to_military(time_string):
	timeMatch = re.match(r'(?P<hour>\d+):(?P<minute>\d+)\s*(?P<ampm>[AMP]+)', time_string)
	return (int(timeMatch.group('hour')) % 12 * 100 + int(timeMatch.group('minute')) + (0, 1200)[timeMatch.group('ampm') == 'PM'])
    
# find_class: returns classes which fit the given parameters
def find_class(year, season, category, timeStart, days):
    connection = sqlite.connect(DATABASE_NAME)
    cursor = connection.cursor()
    
    # validate input data
    if re.search(r'[^a-zA-Z:0-9]+', year + season + category + timeStart + days) is not None:
        return json.dumps({'error': 'sql'})
    
    timeMatch = re.match(r'(?P<hour>\d+):(?P<minute>\d+)\s*(?P<ampm>[AMP]+)', timeStart)
    timeStart = '%02d:%02d %s' % (int(timeMatch.group('hour')), int(timeMatch.group('minute')), timeMatch.group('ampm'))
    
    # form the category filter
    cat_hum = ['AAS','AFRO','AFST','AIS','ANTH','ARCH','ART','ARTD','ARTE','ARTF','ARTH','ARTS','ASST','CHLH','CINE','CLCV','CMN','CW','CWL','EALC','EDPR','EIL','ENGL','ENVS','EOL','EPS','EPSY','ESL','EURO','FAA','GEOG','GER','GLBL','GMC','GS','GWS','HCD','HDES','HDFS','HIST','HRE','HUM','JOUR','JS','LAST','LLS','MDIA','MDVL','MUS','MUSE','NUTR','PHIL','PS','PSYC','REES','REHB','RHET','RLST','RSOC','RST','RUSS','SAME','SCAN','SCR','SLAV','SOC','SPAN','SPED','SWAH','TURK','UKR','WLOF','WRIT','YDSH','ZULU']
    cat_eng = ['ABE','ACES','AE','ASTR','BIOC','BIOE','BIOL','BIOP','BTW','CB','CDB','CEE','CHBE','CHEM','CPSC','CS','CSE','ECE','ECON','ENG','ENGH','ESE','GE','GEOG','GEOL','HORT','IB','IE','LIS','MATH','MCB','ME','MICR','MSE','NEUR','NPRE','NRES','PATH','PBIO','PHYS','PLPA','STAT','TE','TSM']
    catpred = ''
    
    if category == 'humanities':
        catpred = 'AND subject IN ("' + '","'.join(cat_hum) + '")'
    elif category == 'engineering':
        catpred = 'AND subject IN ("' + '","'.join(cat_eng) + '")'
    else:
        catpred = ''
    
    FIND_CLASS_QUERY = 'SELECT year, semester, subject, number, name FROM (uiuc_sections INNER JOIN uiuc_courses ON uiuc_sections.course_pk=uiuc_courses.pk) WHERE semester="%s" AND year="%s" AND time_start="%s" AND days="%s" %s GROUP BY name ORDER BY subject ASC'
    formed_query = FIND_CLASS_QUERY % (season, year, timeStart, days, catpred)
    
    cursor.execute(formed_query)
    res = cursor.fetchall()
    
    return json.dumps(res)
    
# query_class_offers: returns seasons in which the class is offered, for example
# [ {2010, "spring"}, {2008, "fall"}, ... ]
def query_class_offers(className):
    connection = sqlite.connect(DATABASE_NAME)
    cursor = connection.cursor()
	
    classToken = re.match('(?P<department>[a-zA-Z]+)(?P<number>\d+)', className)
    
    classDept = classToken.group('department').upper()
    classNumber = classToken.group('number')
    
    return 0

def query_class(className):
	connection = sqlite.connect(DATABASE_NAME)
	cursor = connection.cursor()
		
	classToken = re.match('(?P<department>[a-zA-Z]+)(?P<number>\d+)', className)

	classDept = classToken.group('department').upper()
	classNumber = classToken.group('number')

	cursor.execute("SELECT * FROM %s WHERE subject=\"%s\" AND number=%s" % (COURSE_TABLE_NAME, classDept, classNumber))
	res = cursor.fetchall()

	if len(res) <= 0:
		return json.dumps({'error': 'class not found'})

	# For each <class> find the corresponding sections and place in section table
	sectionTable = {}

	for row in res:
		rowPk = int(row[0])
		cursor.execute("SELECT * FROM %s WHERE course_pk=%d" % (SECTION_TABLE_NAME, rowPk))
		sectionResult = cursor.fetchall()
		
		for section in sectionResult:
			timeStart = to_military(section[5])
			timeEnd = to_military(section[6])
			
			try:
				sectionTable[section[3]].append(timeStart)
			except KeyError:
				sectionTable[section[3]] = [timeStart]
				
	return json.dumps(sectionTable)
			
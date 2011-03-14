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
			
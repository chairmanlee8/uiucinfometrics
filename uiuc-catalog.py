from pysqlite2 import dbapi2 as sqlite
from collections import defaultdict
import sys
import re

# ---------------------------------------------------
# UIUC Catalog Command Line Utility
# Usage: uiuc-catalog <class>
# ---------------------------------------------------

def to_military(time_string):
	timeMatch = re.match(r'(?P<hour>\d+):(?P<minute>\d+)\s*(?P<ampm>[AMP]+)', time_string)
	return (int(timeMatch.group('hour')) % 12 * 100 + int(timeMatch.group('minute')) + (0, 1200)[timeMatch.group('ampm') == 'PM'])

# Main script:

COURSE_TABLE_NAME = "uiuc_courses"
SECTION_TABLE_NAME = "uiuc_sections"

connection = sqlite.connect('uiuc_course_catalog.db')
cursor = connection.cursor()

if len(sys.argv) < 2:
	print "Usage: uiuc-catalog <class>"
	sys.exit(0)
	
classToken = re.match('(?P<department>[a-zA-Z]+)(?P<number>\d+)', sys.argv[1])

classDept = classToken.group('department')
classNumber = classToken.group('number')

cursor.execute("SELECT * FROM %s WHERE subject=\"%s\" AND number=%s" % (COURSE_TABLE_NAME, classDept, classNumber))
res = cursor.fetchall()

if len(res) <= 0:
	print "No such class."
	sys.exit(0)

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
			
for k, v in sectionTable.iteritems():
	vd = defaultdict(int)
	for x in v: vd[x] += 1
	
	print "%25s {" % k,
	for key in sorted(dict(vd)):
		print "%d: %d," % (key, vd[key]),
	print "}"
		
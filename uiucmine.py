# uiucmine.py
# Script to mine data from uiuc website and populate a sqlite database.
# SQLite table uiuc_courses schema:
# 	(pk, year, semester, subject, number, name)
# 	ex: (1, 2011, "spring", "ABE", "100", "whatever name")
# SQLite table uiuc_sections schema:
#	(pk, course_pk, crn, type, code, timeStart, timeEnd, days, location, instructor, hours)
#	ex: (1, 1, 32512, "lecture", "AL1", time, time, "TR", "blah", "Mr. blah", 3.0)

from uiucinfometrics import *
from pysqlite2 import dbapi2 as sqlite
import time
import sys

COURSE_TABLE_NAME = "uiuc_courses"
SECTION_TABLE_NAME = "uiuc_sections"

connection = sqlite.connect('uiuc_course_catalog.db')
cursor = connection.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + COURSE_TABLE_NAME + "'")
res = cursor.fetchall()

if len(res) <= 0:
	print "Warning: table " + COURSE_TABLE_NAME + " does not exist, creating..."
	cursor.execute("CREATE TABLE " + COURSE_TABLE_NAME + " (pk INTEGER PRIMARY KEY, year INTEGER, semester VARCHAR(16), subject VARCHAR(5), number INTEGER, name VARCHAR(256))")
	
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='" + SECTION_TABLE_NAME + "'")
res = cursor.fetchall()

if len(res) <= 0:
	print "Warning: table " + SECTION_TABLE_NAME + " does not exist, creating..."
	cursor.execute("CREATE TABLE " + SECTION_TABLE_NAME + " (pk INTEGER PRIMARY KEY, course_pk INTEGER, crn INTEGER, type VARCHAR(50), code VARCHAR(8), time_start VARCHAR(24), time_end VARCHAR(24), days VARCHAR(8), location VARCHAR(128), instructor VARCHAR(128), hours DOUBLE)")
	
connection.commit()

#
# Begin populating data table
#

semesters = get_archive_semesters()
resumeTrigger = False
ryear = 0
rseason = ''
rsubject = ''

if 'resume' not in sys.argv:
    resumeTrigger = True
else:
    argindex = sys.argv.index('resume')
    ryear = int(sys.argv[argindex + 2])
    rseason = sys.argv[argindex + 1]
    rsubject = sys.argv[argindex + 3]
    semesters = [(ryear, rseason)]
    

for year, season in semesters:
	if season == 'summer':
		# summer semester is really idiosyncratic, ignore for now...
		continue
		
	subjects = get_subjects(year, season)
	time.sleep(0.5)
	
	# resumeTrigger handling
	if resumeTrigger is False and (year != ryear or season != rseason):
		print "Skipping " + season.upper() + " " + str(year) + "..."
		continue
	
	iidx = 0
	for subject_code, subject_name in subjects:
		iidx += 1
		
		# resumeTrigger handling
		#if resumeTrigger is False and subject_code != rsubject:
		#	print "Skipping " + season.upper() + " " + str(year) + " " + subject_code.upper() + "..."
		#	continue
		#else:
		#	resumeTrigger = True
		
		courses = get_subject_courses(year, season, subject_code)
		time.sleep(0.5)
		
		idx = -1
		for course_number, course_name in courses:
			idx += 1

			# Print progress
			print "%-6s" % season.upper() + " " + str(year) + " %4s%-3d" % (subject_code, course_number) + " [%3d%%]" % int(100.0*(float(idx)/len(courses))) + " [%3d%%]" % int(100.0*(float(iidx)/len(subjects)))
				
			# Insert or update COURSE_TABLE, first see if already exists
			cursor.execute("SELECT * FROM " + COURSE_TABLE_NAME + " WHERE year=? AND semester=? AND subject=? AND number=?", (year, season, subject_code, course_number))
			res = cursor.fetchall()
			
			# if already exists and noupdate is set, then skip over it, continue
			if 'noupdate' in sys.argv and len(res) > 0:
				continue
			
			# if this course has no sections, continue
			sections = get_course_sections(year, season, subject_code, course_number)
			time.sleep(0.5)
			
			if sections is None:
				continue
			
			# okay update it and run the sections
			rowValues = {'year': year, 'semester': season, 'subject': subject_code, 'number': course_number, 'name': course_name}
			
			if len(res) <= 0:
				# INSERT
				cursor.execute("INSERT INTO " + COURSE_TABLE_NAME + "(" + ','.join(rowValues.keys()) + ") VALUES (" + ','.join('?' * len(rowValues.keys())) + ")", tuple(rowValues.values()))
			else:
				# UPDATE
				cursor.execute("UPDATE " + COURSE_TABLE_NAME + " SET " + ','.join([key + '=?' for key in rowValues.keys()]) + " WHERE pk=?", tuple(rowValues.values() + [res[0][0]]))
				
			connection.commit()
			
			for section in sections:
				# Expand the tuple
				ccrn, ctype, ccode, ctimespan, cdays, clocation, cinstructor, chours = section

				# Insert or update SECTION_TABLE
				cursor.execute("SELECT * FROM " + COURSE_TABLE_NAME + " WHERE year=? AND semester=? AND subject=? AND number=?", (year, season, subject_code, course_number))
				res = cursor.fetchall()
				course_pk = int(res[0][0])
				
				cursor.execute("SELECT * FROM " + SECTION_TABLE_NAME + " WHERE course_pk=? AND crn=?", (course_pk, ccrn))
				res = cursor.fetchall()
				
				rowValues = {'course_pk': course_pk, 'crn': ccrn, 'type': ctype, 'code': ccode, 'time_start': time.strftime("%I:%M %p", ctimespan[0]), 'time_end': time.strftime("%I:%M %p", ctimespan[1]), 'days': cdays, 'location': clocation, 'instructor': cinstructor, 'hours': chours}
				
				if len(res) <= 0:
					# INSERT
					cursor.execute("INSERT INTO " + SECTION_TABLE_NAME + "(" + ','.join(rowValues.keys()) + ") VALUES (" + ','.join('?' * len(rowValues.keys())) + ")", tuple(rowValues.values()))
				else:
					# UPDATE
					cursor.execute("UPDATE " + SECTION_TABLE_NAME + " SET " + ','.join([key + '=?' for key in rowValues.keys()]) + " WHERE pk=?", tuple(rowValues.values() + [res[0][0]]))
					
				connection.commit()
				
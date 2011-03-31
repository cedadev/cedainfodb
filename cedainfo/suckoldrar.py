
import psycopg2.psycopg1 as psycopg  #Updated by ASH
import string


import urllib2
import re


from ConfigParser import *



#------------
# string repr of mon number
def smonth(i):
    return "%s-%2.2d-01" % (1990 +i/12, (i % 12) +1)

#-------------





configdict = ConfigParser()
configdict.read('rar.conf')


dbname = configdict.get('database','dbname')
user =  configdict.get('database','user')
password = configdict.get('database','password')
host = configdict.get('database','host')

conn = psycopg.connect("dbname=%s user=%s password=%s host=%s" % (dbname, user, password, host))

cur = conn.cursor()

tt=''
for i in range(128,255): tt += chr(i)
ttable =string.maketrans(tt, " "*127)

def jsonescape(s): 
    if s ==None: s =''
    s = s.replace('\\', '\\\\')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '')
    s = s.replace('\v', ' ')
    s = s.replace('"', '\\"')
    s = s.replace("\t", "\\t")
    s = s.replace("\x92", "'")
    s = s.replace("\xa0", " ")
    s = s.replace("\x0e", " ")
    s = s.translate(ttable)
    s = unicode(s)
    s = str(s)
    return s



#=================
# team table
JSON = open("rardump1.person.json", 'w')
JSON.write('[\n')
person = {}
sql = """select name, username, active, cedar, fedid, stp_name, band FROM cedar_team"""
    
cur.execute(sql)
records = cur.fetchall()

i=1

for rec in records:
    JSON.write( """
  {
     "model": "rar.person",
     "pk":%s,
     "fields": {
        "name": "%s",
	"username": "%s",
	"active": "%s",
	"CEDA": "%s",
	"fedid": "%s",
	"band": "%s"
	}
  },
  """ % (i, rec[0], rec[1], rec[2], rec[3], rec[4], rec[6]) )
    
    person[rec[1]] = i
    i = i+1

 

# write a dummy end record to get the last comma right and end JSON file
JSON.write("""{"model": "rar.person", "pk":10000, "fields": { 
"name": "DELETE ME", "username": " - ", "active": "True", "CEDA": "True",
"fedid": " - ", "band": "A" }} ]""")
JSON.close()

#=======================
# availibility
JSON = open("rardump1.avail.json", 'w')
JSON.write('[\n')

sql = """select username, month, availability FROM cedar_staff_available"""
    
cur.execute(sql)
records = cur.fetchall()

i=1

for rec in records:
    JSON.write( """
  {
     "model": "rar.availability",
     "pk":%s,
     "fields": {
        "person": "%s",
	"month": "%s",
	"value": "%s"
	}
  },
  """ % (i, person[rec[0]], smonth(rec[1]), rec[2]) )

    i = i+1

 

# write a dummy end record to get the last comma right and end JSON file
JSON.write("""{"model": "rar.person", "pk":10000, "fields": { 
"name": "DELETE ME", "username": " - ", "active": "True", "CEDA": "True",
"fedid": " - ", "band": "A" }} ]""")
JSON.close()

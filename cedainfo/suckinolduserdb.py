
import psycopg2.psycopg1 as psycopg  #Updated by ASH
import string

from ConfigParser import *

configdict = ConfigParser()
configdict.read('userdb.conf')


dbname = configdict.get('database','dbname')
user =  configdict.get('database','user')
password = configdict.get('database','password')
host = configdict.get('database','host')

conn = psycopg.connect("dbname=%s user=%s password=%s host=%s" % (dbname, user, password, host))

cur = conn.cursor()


def jsonescape(s): 
    if s ==None: s =''
    s = s.replace('\\', '\\\\')
    s = s.replace('\n', '\\n')
    s = s.replace('\r', '')
    s = s.replace('\v', ' ')
    s = s.replace('"', '\\"')
    s = s.replace("\t", "\\t")
    return s



#=================
#countries
JSON = open("dump1.country.json", 'w')
JSON.write('[\n')
country = {}
sql = """select name, area, isocode from countries"""
    
cur.execute(sql)
records = cur.fetchall()
records.append(('', 'other', 'XX'))

i=1

for rec in records:
    JSON.write( """
  {
     "model": "userdb.country",
     "pk":%s,
     "fields": {
        "name": "%s",
	"area": "%s",
	"isocode": "%s"
	}
  },
  """ % (i, rec[0], rec[1], rec[2]) )
    
    country[rec[0]] = i
    i = i+1

# write a dummy end record to get the last comma right and end JSON file
JSON.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSON.close()

#===============
#institutes
JSON = open("dump2.institute.json", 'w')
JSON.write('[\n')
sql = """select institutekey, name, country, type, link from tbinstitutes"""
    
cur.execute(sql)
records = cur.fetchall()

for rec in records:
    if rec[2] == 'None': c = country['']
    else: c = country[rec[2]]
    
    JSON.write("""
  {
     "model": "userdb.institute",
     "pk":%s,
     "fields": {
        "name": "%s",
	"country": "%s",
	"itype": "%s",
	"link": "%s"
	}
  },
  """ % (rec[0], rec[1], c, rec[3], rec[4]) )

# write a dummy end record to get the last comma right and end JSON file
JSON.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSON.close()



#================
#users
JSON = open("dump3.user.json", 'w')
JSON.write('[\n')
sql = """select userkey, title, surname, othernames, telephoneno, 
emailaddress, comments, endorsedby, degree, field, accountid,
accounttype, encpasswd, md5passwd, webpage, sharedetails, 
datacenter, openid_username_component, openid, department, 
address1, address2, address3, address4, address5, institutekey, startdate
 from tbusers AS u, addresses AS a 
WHERE a.addresskey = u.addresskey
"""
    
cur.execute(sql)
records = cur.fetchall()


for rec in records:
    startdate = ("%s"%rec[26])[0:10]
    if startdate == "None": startdate = "1995-01-01"
    address = string.join(rec[19:25], ', ')
    postcode = ''
    for i in range(24,19,-1):
        if rec[i]:
            postcode = rec[i]
            break
    JSON.write( """
    
  {
     "model": "userdb.user",
     "pk":%s,
     "fields": {
        "title": "%s",
	"firstname": "%s",
	"lastname": "%s",
        "email": "%s", 
        "tel": "%s", 
        "address": "%s",
        "postcode": "%s",
        "webpage": "%s",
        "comments": "%s",
        "endorsedby": "%s",
        "studying_for": "%s",
        "field_of_study": "%s",
        "supervisor": "%s",
        "password_md5": "%s",
        "startdate": "%s",
        "reg_source": "%s",
        "openid": "%s",
        "username": "%s",
        "institute": "%s"
	}
  },
  """ % (rec[0],rec[1],rec[3],rec[2], 
        rec[5],rec[4],address,
        postcode,rec[14],jsonescape(rec[6]),
        rec[7],rec[8],rec[9],rec[7],
        rec[13],
        startdate, rec[16],rec[18],rec[10],
	rec[25]  ))

# write a dummy end record to get the last comma right and end JSON file
JSON.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSON.close()


#================
# roles
JSON = open("dump4.role.json", 'w')

JSON.write( """[
  {
     "model": "userdb.role",
     "pk":1,
     "fields": {
        "name": "Get Data",
	"description": "get data from archive"	}
  },
  {
     "model": "userdb.role",
     "pk":2,
     "fields": {
        "name": "Authoriser",
	"description": "authoriser"	}
  },
  {
     "model": "userdb.role",
     "pk":3,
     "fields": {
        "name": "Membership Veiwer",
	"description": "Veiw membership"	}
  }
  ]
  """  )

JSON.close()

    
#========================
#   groups and applicationprocess
JSONg = open("dump5.group.json", 'w')
JSONg.write('[\n')
JSONap = open("dump6.appproc.json", 'w')
JSONap.write('[\n')
sql = """select datasetid, authtype, grp, grouptype, description,
source, ukmoform, ordr, comments, directory, metdata, 
conditions, defaultreglength, datacentre, infourl 
FROM tbdatasets"""
    
cur.execute(sql)
records = cur.fetchall()

i=1
groups = {}

for rec in records:
    # group records
    JSONg.write("""
  {
     "model": "userdb.group",
     "pk":%s,
     "fields": {
        "name": "%s",
	"description": "%s",
	"valid_from": "",
	"valid_to": "",
	"comments": "%s"
	}
  },
  """ % (i,rec[0], jsonescape(rec[4]), jsonescape(rec[8]) ) )

    # application process records
    JSONap.write("""
  {
     "model": "userdb.applicationprocess",
     "pk":%s,
     "fields": {
        "role": "1",
	"group": "%s",
	"conditions": "%s",
	"defaultreglength": "%s",
	"datacentre": "%s",
	"authtype": "%s"
	}
  },
  """ % (i,i, rec[11], rec[12], rec[13], rec[1] ) )

    groups[rec[0]] = i
    i = i+1

# write a dummy end record to get the last comma right and end JSON file
JSONg.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSONg.close()
JSONap.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSONap.close()


# Licences
    
sql = """select userkey, datasetid, ver, endorsedby, endorseddate,
research, nercfunded, removed, removeddate, grantref, openpub,
extrainfo, expiredate 
FROM tbdatasetjoin"""
    
cur.execute(sql)
records = cur.fetchall()

i=0

for rec in records:
    if rec[8]: removeddate = '"removeddate": "%s",'% ("%s"%rec[8])[0:10] 
    else: removeddate = ""
    if rec[12]: expiredate = '"expiredate": "%s",'% ("%s"%rec[12])[0:10] 
    else: expiredate = ""
    JSON.write("""
  {
     "model": "userdb.licence",
     "pk":%s,
     "fields": {
	"user": "%s",
        "institute": "None",
	"start_date": "%s",
	"end_date": "%s",
	"research": "%s",
	"grantref": "%s",
	"application_process": "%s"
	}
  },
  """ % (i,rec[0],rec[4],rec[12],jsonescape(rec[5]),jsonescape(rec[9]),groups[rec[1]]))


    i = i+1


# write a dummy end record to get the last comma right and end JSON file
JSON.write("""
  {
     "model": "userdb.country",
     "pk":10000,
     "fields": {
        "name": "DELETE ME",
	"area": "other",
	"isocode": "XX"
	}
  }
]
""" )

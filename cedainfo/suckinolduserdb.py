
import psycopg2.psycopg1 as psycopg  #Updated by ASH


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


JSON = open("dump.json", 'w')
JSON.write('[\n')


#countries
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


#institutes
sql = """select institutekey, name, country, type, link from tbinstitutes"""
    
cur.execute(sql)
records = cur.fetchall()

for rec in records:
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
  """ % (rec[0], rec[1], country[rec[2]], rec[3], rec[4]) )




#users
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
    JSON.write( """
    
  {
     "model": "userdb.user",
     "pk":%s,
     "fields": {
        "title": "%s",
	"surname": "%s",
	"othernames": "%s",
        "telephoneno": "%s", 
        "emailaddress": "%s", 
        "comments": "%s",
        "endorsedby": "%s",
        "degree": "%s",
        "field": "%s",
        "accountid": "%s",
        "accounttype": "%s", 
        "encpasswd": "%s",
        "md5passwd": "%s",
        "webpage": "%s",
        "sharedetails": "%s",
        "datacentre": "%s",
        "openid_username_component": "%s",
        "openid": "%s",
        "department": "%s",
        "address1": "%s",
        "address2": "%s",
        "address3": "%s",
        "address4": "%s",
        "address5": "%s",
        "institute": %s,
	"startdate": "%s"
	}
  },
  """ % (rec[0],rec[1],rec[2],rec[3], 
        rec[4],rec[5],jsonescape(rec[6]),rec[7], 
	rec[8],rec[9],rec[10],rec[11],
	rec[12],rec[13],rec[14],rec[15] == -1,
	rec[16],rec[17],rec[18],rec[19],
	rec[20],rec[21],rec[22],rec[23],
	rec[24],rec[25], startdate)  )

# roles (aka groups)
sql = """select datasetid, authtype, grp, grouptype, description,
source, ukmoform, ordr, comments, directory, metdata, 
conditions, defaultreglength, datacentre, infourl 
FROM tbdatasets"""
    
cur.execute(sql)
records = cur.fetchall()

i=1
roles = {}

for rec in records:
    JSON.write("""
  {
     "model": "userdb.role",
     "pk":%s,
     "fields": {
        "name": "%s",
	"authtype": "%s",
	"grouptype": "%s",
	"description": "%s",
	"source": "%s",
	"ukmoform": "%s",
	"comments": "%s",
	"directory": "%s",
	"metdata": "%s",
	"conditions": "%s",
	"defaultreglength": "%s",
	"datacentre": "%s",
	"infourl": "%s"
	}
  },
  """ % (i,rec[0], rec[1], rec[3], jsonescape(rec[4]), 
         rec[5], rec[6] == -1, jsonescape(rec[8]), rec[9],
	 rec[10] == -1, rec[11], rec[12], rec[13], rec[14] ) )
    roles[rec[0]] = i
    i = i+1


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
        "role": "%s",
	"user": "%s",
	"ver": "%s",
	"endorsedby": "%s",
	"endorseddate": "%s",
	"research": "%s",
	"nercfunded": "%s",
	"removed": "%s",
	%s
	"grantref": "%s",
	"grantref": "%s",
	%s
	"extrainfo": "%s"
	}
  },
  """ % (i,roles[rec[1]], rec[0], rec[2], rec[3], 
         ("%s"%rec[4])[0:10],
	 jsonescape(rec[5]), 
	 rec[6] == -1, rec[7] == -1, 
	 removeddate, jsonescape(rec[9]), rec[10], 
	 expiredate, jsonescape(rec[11])  ) )

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

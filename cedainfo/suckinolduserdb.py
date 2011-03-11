
import psycopg2.psycopg1 as psycopg  #Updated by ASH
import string


import urllib2
import re


from ConfigParser import *

configdict = ConfigParser()
configdict.read('userdb.conf')


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
        "studying_for": "%s",
        "field": "%s",
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
        rec[8],rec[9],rec[7],
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
#   groups, conditions and applicationprocess
JSONg = open("dump5.group.json", 'w')
JSONg.write('[\n')
JSONap = open("dump6.appproc.json", 'w')
JSONap.write('[\n')
JSONc = open("dump7.conditions.json", 'w')
JSONc.write('[\n')
sql = """select datasetid, authtype, grp, grouptype, description,
source, ukmoform, ordr, comments, directory, metdata, 
conditions, defaultreglength, datacentre, infourl 
FROM tbdatasets"""
    
cur.execute(sql)
records = cur.fetchall()

# make default conditions record
JSONc.write("""{ "model": "userdb.conditions", "pk":%s, "fields": {"title": "%s", "text": "%s"}},
            """ % (1,'EMPTY conditions', 'No conditions?' ) )

i=1
groups = {}
conditioni = 2
conditions = {}
groupcond = {}

for rec in records:


    conditionsurl = rec[11]
    conditionsurl = string.replace(conditionsurl,'$HTROOT', 'http://badc.nerc.ac.uk')

    # extract conditions of use from web
    if conditionsurl not in conditions.keys(): 
        print "conditions url: %s" % (conditionsurl, )
        try: f = urllib2.urlopen(conditionsurl)
        except:
            conditions[conditionsurl] = 1
	    groupcond[rec[0]] = 1            
        else:
            conditionstext = f.readlines()
            conditionstext = string.join(conditionstext,'')
            conditionstext = jsonescape(conditionstext)
            m = re.search('<title>(.*)</title>', conditionstext, re.I)
            if m: title = m.group(1)
            conditions[conditionsurl] = conditioni
	    groupcond[rec[0]]=conditioni
	    conditioni += 1
            # conditions records
            JSONc.write("""{ "model": "userdb.conditions", "pk":%s, "fields": {"title": "%s", "text": "%s"}},
                  """ % (conditions[conditionsurl],title, conditionstext ) )
    else:
        groupcond[rec[0]]=conditions[conditionsurl]

    # group records
    JSONg.write("""
  {
     "model": "userdb.group",
     "pk":%s,
     "fields": {
        "name": "%s",
	"description": "%s",
	"comments": "%s",
	"infourl": "%s",
	"datacentre": "%s"
	}
  },
  """ % (i,rec[0], jsonescape(rec[4]), jsonescape(rec[8]), rec[14], rec[13] ) )

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
	"authtype": "%s"
	}
  },
  """ % (i,i, conditions[conditionsurl], rec[12],  rec[1] ) )


    print rec[0], conditionsurl, conditions[conditionsurl]


    groups[rec[0]] = i
    i = i+1

  

# write a dummy end record to get the last comma right and end JSON file
JSONg.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSONg.close()
JSONap.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSONap.close()
JSONc.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSONc.close()
iap = i

print groupcond
print
print groups

#===================
# Licences
JSON = open("dump8.licence.json", 'w')
JSON.write('[\n')
    
sql = """select dsj.userkey, dsj.datasetid, dsj.ver, dsj.endorsedby, dsj.endorseddate,
dsj.research, dsj.nercfunded, dsj.removed, dsj.removeddate, dsj.grantref, dsj.openpub,
dsj.extrainfo, dsj.expiredate, i.name, u.emailaddress, dsj.fundingtype 
FROM tbdatasetjoin AS dsj, tbusers AS u, tbinstitutes AS i, addresses AS a 
WHERE dsj.userkey = u.userkey 
  AND a.addresskey = u.addresskey
  AND a.institutekey = i.institutekey"""
    
cur.execute(sql)
records = cur.fetchall()

i=0

for rec in records:
    if rec[12]: expiredate = rec[12] 
    else: expiredate = "2020-01-01"
    if rec[7] == -1 :status='expired' 
    else: status='accepted'
    JSON.write("""
  {
     "model": "userdb.licence",
     "pk":%s,
     "fields": {
	"user": "%s",
        "institute": "%s",
	"start_date": "%s",
	"end_date": "%s",
	"research": "%s",
	"grantref": "%s",
	"role": "%s",
	"group": "%s",
	"conditions": "%s",
	"email": "%s",
	"funding_type": "%s",
	"request_date": "%s",
	"extrainfo": "%s",
	"fromhost": "%s",
	"status": "%s"
	}
  },
  """ % (i,rec[0],jsonescape(rec[13]),
         rec[4],expiredate,jsonescape(rec[5]),jsonescape(rec[9]),1,groups[rec[1]],groupcond[rec[1]],
	 rec[14], rec[15],rec[4],jsonescape(rec[11]), '?', status))


    i = i+1

# write a dummy end record to get the last comma right and end JSON file
JSON.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSON.close()
ilicence = i

#=========================
# priveleges

JSON = open("dump9.priv.json", 'w')
JSON.write('[\n')
    
sql = """select p.userkey, p.type, p.datasetid, p.comment, i.name 
FROM privilege AS P, tbusers AS u, tbinstitutes AS i, addresses AS a 
WHERE p.userkey = u.userkey 
  AND a.addresskey = u.addresskey
  AND a.institutekey = i.institutekey"""
    
cur.execute(sql)
records = cur.fetchall()

# these are more licences. Need to keep i form previous licence block 

for rec in records:
    expiredate = "2020-01-01"
    startdate = "2009-01-01"
    reqdate = "2009-01-01"
    if rec[1] == 'authorise': role = 2
    elif rec[1] == 'viewusers': role =3
    else: raise "Unknown role type"

    # licence
    if rec[2] not in groups.keys(): continue
    JSON.write("""
  {
     "model": "userdb.licence",
     "pk":%s,
     "fields": {
	"user": "%s",
        "institute": "%s",
	"start_date": "%s",
	"end_date": "%s",
	"research": "%s",
	"grantref": "%s",
	"role": "%s",
	"group": "%s",
	"status": "%s",
	"request_date": "%s"
	}
  },
  """ % (ilicence,rec[0],jsonescape(rec[4]),
         startdate,expiredate,jsonescape(rec[3]),'',
	 role,groups[rec[2]], 'accepted', reqdate))

    ilicence = ilicence+1

# write a dummy end record to get the last comma right and end JSON file
JSON.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSON.close()



#=========================
# licence requests

JSON = open("dump10.licencereq.json", 'w')
JSON.write('[\n')
    
sql = """select id, userkey, datasetid, requestdate, research, nercfunded,
fundingtype, grantref, openpub, extrainfo, fromhost, status
FROM datasetrequest AS dr
WHERE status <> 'accepted' 
""" 
    
cur.execute(sql)
records = cur.fetchall()


# these are more licences. Need to keep i form previous licence block 

for rec in records:
    # licence request
    if rec[3]: reqdate = rec[3] 
    else: reqdate = "2000-01-01"
    if rec[2] not in groups.keys(): continue
    JSON.write("""
  {
     "model": "userdb.licence",
     "pk":%s,
     "fields": {
	"user": "%s",
        "request_date": "%s",
	"research": "%s",
	"grantref": "%s",
	"role": "%s",
	"group": "%s",
	"conditions": "%s",
	"extrainfo": "%s",
	"fromhost": "%s",
	"status": "%s"
	}
  },
  """ % (ilicence, rec[1], reqdate, jsonescape(rec[4]),
         jsonescape(rec[7]), 1, groups[rec[2]], groupcond[rec[2]] ,
	 jsonescape(rec[9]),rec[10],rec[11] ))

    ilicence = ilicence+1

# write a dummy end record to get the last comma right and end JSON file
JSON.write('{"model": "userdb.country", "pk":10000, "fields": { "name": "DELETE ME",	"area": "other", "isocode": "XX"}} ]')
JSON.close()


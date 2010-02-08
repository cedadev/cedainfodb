
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
address1, address2, address3, address4, address5, institutekey
 from tbusers AS u, addresses AS a 
WHERE a.addresskey = u.addresskey
"""
    
cur.execute(sql)
records = cur.fetchall()


for rec in records[:-1]:
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
        "institutekey": "%s"
	}
  },
  """ % rec  )

rec = records[-1]
JSON.write("""
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
        "institutekey": "%s"

  }
  """ % rec )

 
#end JSON file  
JSON.write(']\n')


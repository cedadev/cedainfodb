
import os
import sys


import psycopg2

key_connection = psycopg2.connect(dbname="ceda_accounts", 
                                host="db3-panfs.ceda.ac.uk",
                                user="ceda_accounts", 
                                password="3QagwfMw2cF72OmqNvUC")
key_cursor = key_connection.cursor()


udb_connection = psycopg2.connect(dbname="userdb", 
                                host="db3-panfs.ceda.ac.uk",
                                user="readonly_userdb", 
                                password="rqg739t")
udb_cursor = udb_connection.cursor()



def udb_emails ():

    sql = "select distinct lower(emailaddress) from tbusers where accounttype = 'Web' and accountid !='' order by lower(emailaddress)"

    udb_cursor.execute(sql)
    recs = udb_cursor.fetchall()

    udb_emails = []

    for rec in recs:
        if rec[0]:
            udb_emails.append(rec[0])

    return udb_emails

def key_emails ():
    
    sql = "select distinct email from user_entity order by email"
    key_cursor.execute(sql)
    recs = key_cursor.fetchall()

    keycloak_emails = []

    for rec in recs:
       if rec[0]:
           keycloak_emails.append(rec[0])  
       
    return keycloak_emails
       
def udb_user_details (email):

    details = {}
    sql = "select userkey, accountid, startdate, jasminaccountid from tbusers where lower(emailaddress) = '%s'" % email
    udb_cursor.execute(sql)
    rec = udb_cursor.fetchone()
    
    details['userkey'] = rec[0]
    details['accountid'] = rec[1]
    details['startdate'] = rec[2]
    details['jasminaccountid'] = rec[3]
	        
    return details
     

udb_emails = udb_emails()
print ('Udb emails: ', len(udb_emails))


key_emails = key_emails()
print ('Keycloak emails: ', len(key_emails))





diff1 = []
for email in udb_emails:
    if email not in key_emails:
        diff1.append(email)

print('In userdb but not in keycloak: ') 

for email in diff1:
    details = udb_user_details(email)
    
    print (email, details['accountid'], details['startdate'], details['jasminaccountid'])

sys.exit()


diff2 = []
for email in key_emails:
    if email not in udb_emails:
        diff2.append(email)
 
print ('In keycloak but not in userdb: ') 
print(diff2)

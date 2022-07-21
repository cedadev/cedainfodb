import sys

from udbadmin.models import User
from django.db import connections

def run():

    sql = """
    select distinct emailaddress from tbusers where emailaddress in 
    (SELECT emailaddress from tbusers group by emailaddress having count(emailaddress) > 1)
    """
    
    with connections['userdb'].cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
    
    for row in rows:  
        email = row[0]
        
        users = User.objects.filter(emailaddress=email, accounttype='Web')  
        

        if len(users) == 2:
        
#           
#
                  datasets_0 = len(users[0].datasets(removed=True))
                  datasets_1 = len(users[1].datasets(removed=True))
#                  
                  if datasets_0 >= 0 and datasets_1 >= 0:	
#
                      print (users[0].emailaddress, users[0].userkey, users[0].accountid,  datasets_0, users[0].startdate, users[0].secret_data)
                      print (users[1].emailaddress, users[1].userkey, users[1].accountid,  datasets_1, users[1].startdate, users[1].secret_data)	   
#                      print (min(users[0].userkey, users[1].userkey), ",")
           #           for user in users:
           #               print (user.emailaddress, user.userkey, user.accountid, user.accounttype)
           #
                      print (min(users[0].userkey, users[1].userkey), ",")


#    for p in User.objects.all():

#    sql = """
#    select * from tbusers where emailaddress in (SELECT emailaddress from tbusers group by emailaddress having count(emailaddress) > 1) and accountid != ''
#    """
#    for p in User.objects.raw(sql):
#        datasets = len(p.datasets(removed=True))
#
#        if datasets == 0:
#            print (p.accountid, p.userkey, datasets)
 

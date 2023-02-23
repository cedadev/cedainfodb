import sys

from udbadmin.models import User
from django.db import connections

def run():

    sql = """
select distinct lower(emailaddress) from tbusers where lower(emailaddress) in 
(
SELECT lower(emailaddress) from tbusers group by lower(emailaddress) having count(emailaddress) > 1)

    """
    
    with connections['userdb'].cursor() as cursor:
        cursor.execute(sql)
        rows = cursor.fetchall()
    
    for row in rows:  
        email = row[0]
        
        users = User.objects.filter(emailaddress__iexact=email, accounttype='Web')  
        

        if len(users) > 1:
#        
#           #
#
                    for user in users:
                        datasets = len(user.datasets(removed=False))
                        print (user.accountid, datasets)
#                        print (user.emailaddress, user.userkey, user.accountid,  datasets, user.startdate, user.secret_data)
                    print (' ')
#                      print (min(users[0].userkey, users[1].userkey), ",")
           #           for user in users:
           #               print (user.emailaddress, user.userkey, user.accountid, user.accounttype)
           #
#                      print (min(users[0].userkey, users[1].userkey), ",")


#    for p in User.objects.all():

#    sql = """
#    select * from tbusers where emailaddress in (SELECT emailaddress from tbusers group by emailaddress having count(emailaddress) > 1) and accountid != ''
#    """
#    for p in User.objects.raw(sql):
#        datasets = len(p.datasets(removed=True))
#
#        if datasets == 0:
#            print (p.accountid, p.userkey, datasets)
 

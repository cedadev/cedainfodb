import sys
#sys.path.append('/home/badc/software/pythonlib/userdb')

from udbadmin.models import User


def run():

    print('hello')
    
    for line in sys.stdin:
        print('bbb')
        username = line.strip()
        print(username)
        try: 
            user = User.objects.get(accountid=username)
        except:
            print('ERROR: %s not found' % username)

        print(user.accountid, user.emailaddress.lower())

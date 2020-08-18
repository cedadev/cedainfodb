#
# Can be used as a template for adding a dataset to multiple users. Make sure that the users don't already have access to the dataset (otherwise
# there may be a problem with the version number) 
#
from udbadmin.models import User

FILE      =  "users.lis"
DATASETID =  "xxx"
ENDORSEDBY = "Andrew Harwood"
RESEARCH  =  "Added retrospectively"
EXPIREDATE = "dd-mmm-yyyy"

def process(infile, datasetid):

    f = open(infile, 'r')

    for line in f:
        username = line.strip()

        try: 
            user = User.objects.get(accountid=username)

            print("insert into tbdatasetjoin (userkey, datasetid, ver, endorsedby, endorseddate, expiredate, research) values (", end=' ')            
            print("%s, '%s', %s, '%s', '%s', '%s', '%s'" % (user.userkey, datasetid, 1,  ENDORSEDBY, "now", EXPIREDATE, RESEARCH), end=' ')

            print(")")
        except:
            print('Not Found: %s' % username)
  
    f.close()

def run():      
    process(FILE, DATASETID)

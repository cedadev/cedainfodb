#
# Can be used as a template for adding a dataset to multiple users. Make sure that the users don't already have access to the dataset (otherwise
# there may be a problem with the version number) 
#
from udbadmin.models import User

DATASETID = "system-login"
ENDORSEDBY = "Andrew Harwood"
RESEARCH  =  "Added retrospectively based on content of external NIS passwd file"
EXPIREDATE = "31-Dec-2013"

f = open('users.lis', 'r')

def run():

    for line in f:
        username = line.strip()
    #   print username
        try: 
            user = User.objects.get(accountid=username)
            if user.hasDataset("ceda"):
               print "insert into tbdatasetjoin (userkey, datasetid, ver, endorsedby, endorseddate, expiredate, research) values (",            
               print "%s, '%s', %s, '%s', '%s', '%s', '%s'" % (user.userkey, DATASETID, 1,  ENDORSEDBY, "now", EXPIREDATE, RESEARCH),
            
               print ")"
        except:
            pass
        

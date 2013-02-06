'''
This module contains routines used for generating LDAP/NIS password 
and group file information from the userdb.
Django views that make use of these routines are stored separately.
'''

from models import *


ARCHIVE_ACCESS_GROUPS = {"cmip5_research": {"gid": 26059, "datasets" : ["cmip5_research"]},
                         "esacat1":        {"gid": 26017, "datasets" : ["aatsr_multimission"]},                         
                         "ecmwf":          {"gid": 26018, "datasets" : ["era", "ecmwfop"]},
                         "ukmo" :          {"gid": 26019, "datasets" : ["surface"]},
                         "eurosat":        {"gid": 26021, "datasets" : ["metop_iasi"]},
                         "open":           {"gid": 26020, "datasets" : []},
}
#
# The following users should be a member of all archive access groups
#
ARCHIVE_ACCESS_STANDARD_USERS = ("badc", "prototype")

def is_ldap_user (user):    
    ''' Checks if the user should be in the LDAP system'''

    if user.isJasminCemsUser() or user.hasDataset("system-login"):
        return True
    else:
        return False    

def all_users():
    '''Returns user objects for all LDAP users'''
    
    all_users = User.objects.filter(uid__gt=0)
    
    users = []
    
    for user in all_users:
        if is_ldap_user(user):
            users.append(user)

    return users        


def getDatasetUsers(datasetids):

    '''Returns an array of user objects for users who currently have access to the given dataset(s).
    argument can be either a single dataset id, or an array of datasetids. If more than one datasetid is
    given then this routine returns the list of users who can access any of the datasets. Duplicate users
    are removed from the list.''' 
 
    if isinstance(datasetids, basestring):
        datasetids = [datasetids]
       
    users    = []
    userkeys = []
    
    for datasetid in datasetids:
         
        udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(removed=0)     

        for udj in udjs:
            user = udj.userkey

            if is_ldap_user(user):
                if not user.userkey in userkeys:
                    users.append(user)
                    userkeys.append(user.userkey)

    return users


def checkUid ():
    ''' Returns any users which do not have a uid set'''
   
    users = all_users()

    badUsers = []
    for user in users:
        if not user.uid > 0:
            badUsers.append(user)

    return badUsers

def checkGroups():  

    datasets = Dataset.objects.all().order_by('datasetid')
    
    badUsers = []
    
    for dataset in datasets:
    
        if dataset.datasetid.startswith('gws_'):
            print dataset.datasetid
            users = getDatasetUsers(dataset.datasetid)
            
            for user in users:
                print '   ', user.accountid
                if not (user.hasDataset("system-login") or user.hasDataset("jasmin-login") or user.hasDataset("cems-login")):                 
                    badUsers.append(user)
    return badUsers
                         
                
#----------------------- The following routines are used for generating the contents of the NIS password and group files

def userAccountsString(users):

    '''Converts a list of user objects into a comma separated list of accounts in alphabetical order, removing
       any duplicates.'''
  
    accounts = []

    for user in users:
        if user.accountid not in accounts:
            accounts.append(user.accountid)

    accounts.sort()
    accountsString = ",".join(accounts)
    return accountsString       


def dataset_group_string (datasetid):
    """
    For given datasetid returns the line that should appear in the NIS group file
    """    
    
    dataset = Dataset.objects.get(datasetid=datasetid)

    record = '%s:*:%s:' % (dataset.grp, dataset.gid)
        
    users = getDatasetUsers(datasetid)
    record = record + userAccountsString(users)
    
    return record

def open_group_string():
    ''''Returns line for "open" group for NIS group file'''
    
    users = all_users()
    record = 'open:*:' + str(ARCHIVE_ACCESS_GROUPS["open"]["gid"]) + ':' + userAccountsString(users)
    return record

def generate_all_nis_groups ():
    '''Generate text for NIS group file for all groups controlled by the userdb'''
     
    record = ''
#
#      Generate datasets
#       

    datasets = Dataset.objects.all().filter(gid__gt=0).order_by('grp')
    
    for dataset in datasets:
        record = record + dataset_group_string (dataset.datasetid) + '\n'

#
#       Generate archive access groups
#

    for accessGroup in ARCHIVE_ACCESS_GROUPS.keys():
        if accessGroup == 'open':
            continue
            
        users = getDatasetUsers(ARCHIVE_ACCESS_GROUPS[accessGroup]["datasets"])
        accountsString = userAccountsString(users)
        
        additionalUsers = ",".join(ARCHIVE_ACCESS_STANDARD_USERS)
        
        record = record + accessGroup + ':*:' + str(ARCHIVE_ACCESS_GROUPS[accessGroup]["gid"]) + ':' + accountsString + "\n";

#
#      Generate 'open' data access group
#

    record = record + open_group_string()
                        
    return record
       

'''
This module contains routines used for generating LDAP/NIS password 
and group file information from the userdb.
Django views that make use of these routines are stored separately.
'''
from operator import attrgetter

from models import *

ARCHIVE_ACCESS_GROUPS = {"cmip5_research": {"gid": 26059, "datasets" : ["cmip5_research"]},
                         "esacat1":        {"gid": 26017, "datasets" : ["aatsr_multimission", "atsrubt"]},                         
                         "ecmwf":          {"gid": 26018, "datasets" : ["era", "ecmwfop"]},
                         "ukmo" :          {"gid": 26019, "datasets" : ["surface"]},
                         "eurosat":        {"gid": 26021, "datasets" : ["metop_iasi"]}
                         }
#
# GID for 'open' group
#
OPEN_GID = 26020
#
# Default group id for account
#
DEFAULT_GID = 26030
#
# Default shell for accont
DEFAULT_SHELL = "/bin/bash" 

#
# The following users should be a member of all archive access groups
#
ARCHIVE_ACCESS_STANDARD_USERS = ["badc", "prototype", "cwps"]

def is_ldap_user (user):    
    ''' Checks if the user should be in the LDAP system'''

    if user.hasDataset("system-login") or user.isJasminCemsUser():
        return True
    else:
        return False    

def user_shell (user):
    ''' Returns shell to be used for user. If no specific value has been set 
        for user then use default'''
        
    if user.shell:
        return user.shell
    else:
        return DEFAULT_SHELL

def user_gid (user):
    ''' Returns initial group to be used for user. If no specific value has been set 
        for user then use default'''
        
    if user.gid:
        return user.gid
    else:
        return DEFAULT_GID
        
def user_home_directory (user):
    ''' Returns home directory to be used for user. If no specific value has been set 
        for user then use default'''
        
    if user.home_directory:
        return user.home_directory
    else:
        return "/home/users/%s" % user.accountid
        
             

def all_users(order_by="userkey"):
    '''Returns user objects for all LDAP users. For efficiency this is done using an sql query.
       optionally the results can be ordered by the given field'''

    sql = "select distinct tbusers.* from tbusers, tbdatasetjoin where (tbusers.userkey=tbdatasetjoin.userkey)" + \
          "and tbdatasetjoin.removed=0 and ((datasetid='jasmin-login') or (datasetid='system-login') or (datasetid='cems-login')) " + \
          "and tbusers.uid > 0 order by %s" % order_by
    users = User.objects.raw(sql)
    
    return users

def all_users_userkeys():
    '''Returns array of userkeys of all LDAP users'''
    
    userkeys = []
    
    users = all_users()
    
    for user in users:
        userkeys.append(user.userkey)

    return userkeys

def get_dataset_users(datasetids):

    '''Returns an array of user objects for users who currently have access to the given dataset(s).
    argument can be either a single dataset id, or an array of datasetids. If more than one datasetid is
    given then this routine returns the list of users who can access any of the datasets. Duplicate users
    are removed from the list.''' 
 
    if isinstance(datasetids, basestring):
        datasetids = [datasetids]
#
#      Get usekeys of all users who have an ldap account
#    
    all_valid_userkeys = all_users_userkeys()

    users    = []
    userkeys = []
        
    for datasetid in datasetids:       

        udjs = Datasetjoin.objects.filter(datasetid=datasetid).filter(removed=0)     
        
        for udj in udjs:
            user = udj.userkey

            if user.userkey not in all_valid_userkeys:
                continue
            if user.userkey in userkeys:
                continue
                
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
            users = get_dataset_users(dataset.datasetid)
            
            for user in users:
                print '   ', user.accountid
                if not (user.hasDataset("system-login") or user.hasDataset("jasmin-login") or user.hasDataset("cems-login")):                 
                    badUsers.append(user)
    return badUsers
                         
def ldap_group_record(datasetid):
    '''Returns LDAP record for a group'''
    
    record = ''
    
    try:
        dataset = Dataset.objects.get(datasetid=datasetid)
    except:
        return 
            
    record = "dn: cn=%s,ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk\n" % dataset.grp
    record = record + 'objectClass: posixGroup\n'
    record = record + 'objectClass: top\n'
    record = record + 'cn: %s\n' % dataset.grp
    record = record + 'gidNumber: %s\n' % dataset.gid
    record = record + 'description: cluster:ceda-external\n'
    
    users = get_dataset_users(datasetid)
    users.sort(key=attrgetter('accountid'))
        
    for user in users:
       record = record + 'memberUid: ' + user.accountid + '\n'
  
    return record

def ldap_open_group_record():
    '''Returns LDAP record for open group'''
    
    record = ''

    record = "dn: cn=open,ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk\n"
    record = record + 'objectClass: posixGroup\n'
    record = record + 'objectClass: top\n'
    record = record + 'cn: open\n'
    record = record + 'gidNumber: ' + str(OPEN_GID) + '\n'
    record = record + 'description: cluster:ceda-external\n'
    record = record + 'description: cluster:ceda-internal\n'
    
    all = all_users()
    
    accounts = []
    
    for user in all:
       accounts.append(user.accountid)
       
    accounts = accounts + ARCHIVE_ACCESS_STANDARD_USERS

    for account in sorted(accounts):
       record = record + 'memberUid: ' + account + '\n'
        
    return record   

def ldap_archive_access_group_record(datasetid):

    record = ''
    
    if not datasetid in ARCHIVE_ACCESS_GROUPS.keys():
        return

    record = "dn: cn=%s,ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk\n" % datasetid
    record = record + 'objectClass: posixGroup\n'
    record = record + 'objectClass: top\n'
    record = record + 'cn: %s\n' % datasetid
    record = record + 'gidNumber: ' + str(ARCHIVE_ACCESS_GROUPS[datasetid]["gid"]) + '\n'
    record = record + 'description: cluster:ceda-external\n'
    record = record + 'description: cluster:ceda-internal\n'
        
    users = get_dataset_users(ARCHIVE_ACCESS_GROUPS[datasetid]["datasets"]) 
    
    accounts = []
    
    for user in users:
        accounts.append(user.accountid)
        
    accounts = accounts  + ARCHIVE_ACCESS_STANDARD_USERS

    for account in accounts:
        record = record + 'memberUid: ' + account + '\n'
         
    return record  
    
def ldap_user_record(accountid):
    '''Returns LDAP record for given user'''
    
    
    record = ''
    
    try:
        user = User.objects.get(accountid=accountid)
    except:
        return "%s not found" % accountid
            
    if not is_ldap_user (user):
        return 'Not LDAP user'
    
    if not user.uid > 0:
        return 'uid not set for %s' % accountid
        
    record = "dn: cn=%s,ou=ceda,ou=People,o=hpc,dc=rl,dc=ac,dc=uk\n" % user.accountid
       
    record = record + 'loginShell: %s\n' % user_shell(user)
    record = record + 'sn: %s\n' % user.surname
    record = record + 'objectClass: top\n'
    record = record + 'objectClass: person\n'
    record = record + 'objectClass: posixAccount\n'
    record = record + 'objectClass: ldapPublicKey\n'
    record = record + 'objectClass: rootAccessGroup\n'
    record = record + 'gidNumber: %s\n' % user_gid(user)
    record = record + 'uid: %s\n' % user.accountid
    record = record + 'gecos: %s %s %s\n' % (user.title, user.othernames, user.surname)   
    record = record + 'uidNumber: %s\n' % user.uid      
    record = record + 'cn: %s\n' % user.accountid
    record = record + 'homeDirectory: %s\n' % user_home_directory(user)
    record = record + 'sshPublicKey: %s\n' % user.public_key  
         
    return record   
    
    
                          
#----------------------- The following routines are used for generating the contents of the NIS password and group files

def userAccountsString(users, extraAccounts=[]):

    '''Converts a list of user objects into a comma separated list of accounts in alphabetical order, removing
       any duplicates.'''
  
    accounts = []

    for user in users:
        if user.accountid not in accounts:
            accounts.append(user.accountid)

    accounts.extend(extraAccounts)
       
    accounts.sort()
    accountsString = ",".join(accounts)
    return accountsString       


def dataset_group_string (datasetid):
    """
    For given datasetid returns the line that should appear in the NIS group file
    """    
    
    dataset = Dataset.objects.get(datasetid=datasetid)

    record = '%s:*:%s:' % (dataset.grp, dataset.gid)
        
    users = get_dataset_users(datasetid)
    record = record + userAccountsString(users)
    
    return record

def open_group_string():
    ''''Returns line for "open" group for NIS group file'''
    
    users = all_users()
    record = 'open:*:' + str(OPEN_GID) + ':' + \
          userAccountsString(users, extraAccounts=ARCHIVE_ACCESS_STANDARD_USERS)
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
        users = get_dataset_users(ARCHIVE_ACCESS_GROUPS[accessGroup]["datasets"])
        accountsString = userAccountsString(users, extraAccounts=ARCHIVE_ACCESS_STANDARD_USERS)
        record = record + accessGroup + ':*:' + str(ARCHIVE_ACCESS_GROUPS[accessGroup]["gid"]) + ':' + accountsString + "\n";
#
#      Generate 'open' data access group
#

    record = record + open_group_string()
                        
    return record
       

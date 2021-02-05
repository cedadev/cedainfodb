'''
This module contains routines used for generating LDAP/NIS password 
and group file information from the userdb.
Django views that make use of these routines are stored separately.
'''
from operator import attrgetter
import os
import tempfile
import subprocess
from unidecode import unidecode

from django.conf import settings

from .models import *
from . import LDAP

#EXCLUDE_USERS = ['aharwood', 'mpryor', 'gparton', 'gpp02', 'mpritcha', 'wtucker', 'rsmith013', 'pjkersha', 'fchami']
EXCLUDE_USERS = []
#
# The following users should be a member of all archive access groups
#
ARCHIVE_ACCESS_STANDARD_USERS = ["badc", "prototype", "cwps", "archread", "archive"]


ARCHIVE_ACCESS_GROUPS = {"cmip5_research": {"gid": 26059, "datasets" : ["cmip5_research", "cmip3", "cmip3_ukmo"]},
                         "esacat1":        {"gid": 26017, "datasets" : ["aatsr_multimission", "atsrubt", "mipas", "sciamachy"]},                         
                         "ecmwf":          {"gid": 26018, "datasets" : ["era", "ecmwfop", "ecmwftrj", "era4t", "ecmwfera"]},
#                         "ukmo" :          {"gid": 26019, "datasets" : ["surface"]},
                         "eurosat":        {"gid": 26021, "datasets" : ["metop_iasi", "gome-2"]},
                         
                         "ukmo_wx":        {"gid": 26078, "datasets" : ["africa_lam",
                                                                        "assim",
                                                                        "nimrod",
                                                                        "radios",
                                                                        "surface",
                                                                        "synop",
                                                                        "ukmo-metdb",
                                                                        "um",
                                                                        "nimrod"]},
                         
                         "ukmo_clim":      {"gid": 26079, "datasets" : ["cet",
                                                                        "climod", 
                                                                        "gmslp", 
                                                                        "gosta", 
                                                                        "hadat", 
                                                                        "hadcm3con", 
                                                                        "hadgem1", 
                                                                        "hadisst", 
                                                                        "hadrt", 
                                                                        "hadsst2", 
                                                                        "height", 
                                                                        "higem", 
                                                                        "link", 
                                                                        "mslp",
                                                                        "hadgem1-a1b", 
                                                                        "hadgem1-ctl"]
                                           }
                         
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


def userdb_managed_ldap_groups ():
    """
    Returns list of group names from ldap that are to be controlled via the userdb. This list is used to filter out the groups of interest from the
    ldap server.
    """ 
    
    groups = ["open"]
       
    for group in list(ARCHIVE_ACCESS_GROUPS.keys()):
        groups.append(group)

    datasets = userdb_managed_ldap_datasets()
    
    for dataset in datasets:
        groups.append(dataset.grp)

    return groups
    
def userdb_managed_ldap_datasets ():
    """
    Returns dataset objects for any datasets that are to control ldap groups. These are in addition to the archive access groups (which don't exist
    as records in the userdb.
    """
    datasets = []   
    
#    datasets = Dataset.objects.all().filter(gid__gt=0).exclude(authtype='jasmin-portal').order_by('grp')
#    datasets = Dataset.objects.all().filter(gid__gt=0).exclude(datasetid__startswith='gws_').order_by('grp')
#    datasets = Dataset.objects.all().filter(gid__gt=0).order_by('grp')
    datasets = Dataset.objects.all().filter(gid__gt=0).exclude(authtype='jasmin-portal').order_by('grp')

    return datasets    

def udb_archive_access_datasets():
    """
    Returns dataset objects for all udb archive datasets that control ldap archive access groups
    """
    datasetids = []
    datasets = []
        
    for item in list(ARCHIVE_ACCESS_GROUPS.keys()):
        datasetids.extend(ARCHIVE_ACCESS_GROUPS[item]["datasets"])

    datasetids.sort()
    
    for datasetid in datasetids:
        try:
            datasets.append(Dataset.objects.get(datasetid=datasetid))
        except:
            pass
    
    return datasets    

def userdb_managed_datasetids ():
    """
    Returns a list of all datasetids for userdb datasets that map onto ldap groups
    """
    datasetids = []
    
    for item in list(ARCHIVE_ACCESS_GROUPS.keys()):
        datasetids.extend(ARCHIVE_ACCESS_GROUPS[item]["datasets"])

    datasets = userdb_managed_ldap_datasets()

    for dataset in datasets:
        datasetids.append(dataset.datasetid)

    return datasetids

def is_ldap_user (user):    
    ''' Checks if the user should be in the LDAP system'''

    if user.hasDataset("system-login") or user.hasDataset("ldap_system_user") or user.hasDataset("vm_access_ceda_internal") or user.isJasminCemsUser():
        return True
    else:
        return False    

def user_shell (user):
    ''' Returns shell to be used for user. If no specific value has been set 
        for user then use default'''
        
    if user.shell:
        return user.shell.strip()
    else:
        return DEFAULT_SHELL

def user_gecos (user):
    '''Returns gecos string for user'''
 
    return '%s %s' % (unidecode(user.othernames), unidecode(user.surname))   
 
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
        return user.home_directory.strip()
    else:
        return "/home/users/%s" % user.accountid

def user_passwd_file_entry (user, overide_shell=None):
    '''Returns passwd file entry for user. Note that it is up to the calling
       program to determin if the user should actually have an entry in a 
       passwd file'''

    gid   = user_gid(user)
    gecos = user_gecos(user)  
    home  = user_home_directory(user)


    if overide_shell:
        shell = overide_shell
    else:
        shell = user_shell(user)

    return "%s:x:%s:%s:%s:%s:%s" % (user.accountid, user.uid, gid, gecos, home, shell)

def all_jasmin_cems_users(order_by="userkey"):
    '''Returns user objects for all jasmin/cems users according to the userdb'''

    sql = "select distinct tbusers.* from tbusers, tbdatasetjoin where (tbusers.userkey=tbdatasetjoin.userkey)" + \
          "and tbdatasetjoin.removed=0 and ((datasetid='jasmin-login') or " + \
          "(datasetid='cems-login') or (datasetid='commercial-login') ) " + \
          "order by %s" % order_by

    users = User.objects.raw(sql)

    return users

def all_users(order_by="userkey"):
    '''Returns user objects for all LDAP users. For efficiency this is done using an sql query.
       optionally the results can be ordered by the given field'''

    sql = "select distinct tbusers.* from tbusers where tbusers.jasminaccountid !=''" + \
          "order by %s" % order_by
    
#    sql = "select distinct tbusers.* from tbusers, tbdatasetjoin where (tbusers.userkey=tbdatasetjoin.userkey)" + \
#          "and tbdatasetjoin.removed=0 and ((datasetid='jasmin-login') or " + \
#          "(datasetid='vm_access_ceda_internal') or (datasetid='system-login') or (datasetid='cems-login')) " + \
#          "and tbusers.uid > 0 order by %s" % order_by

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
 
    if isinstance(datasetids, str):
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
#
#           Skip if no user for this record (it can happen!)
#
            if not hasattr(udj, 'userkey'):
                continue
 
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
            print(dataset.datasetid)
            users = get_dataset_users(dataset.datasetid)
            
            for user in users:
                print('   ', user.accountid)
                if not (user.hasDataset("system-login") or \
                        user.hasDataset("jasmin-login") or \
                        user.hasDataset("cems-login") or \
                        user.hasDataset("commercial-login")):                 
                    badUsers.append(user)
    return badUsers

def ldap_all_group_records (add_additions_file=True):
    '''
    Returns ldap record string for all ldap groups
    '''

##    datasets = Dataset.objects.all().filter(gid__gt=0).filter(datasetid='gws_nceo_generic').order_by('grp')
##    datasets = Dataset.objects.all().filter(gid__gt=0).exclude(authtype='jasmin-portal').order_by('grp')
    datasets = userdb_managed_ldap_datasets ()
    
    record = ''
        
    for dataset in datasets:
        record = record + ldap_group_record(dataset.datasetid)                
        record = record + '\n'
    

    for datasetid in list(ARCHIVE_ACCESS_GROUPS.keys()):
        record = record + ldap_archive_access_group_record(datasetid)
        record = record + '\n'
        
    record = record + ldap_open_group_record()
    record = record + '\n'

    if add_additions_file:
        if os.path.exists(settings.ADDITIONAL_LDAP_GROUP_FILE):
            f = open(settings.ADDITIONAL_LDAP_GROUP_FILE, "r")

            additional_groups = f.read()
            f.close()
            record = record + additional_groups    
    
    return record


def ldap_all_user_records (write_root_access=True, add_additional_users=True):
    '''
    Returns ldap record string for all ldap users
    '''
    record = ''
        
    users =  all_users(order_by="accountid")
    
    for user in users:
        if user.accountid not in EXCLUDE_USERS and user.uid > 0:
            record = record + ldap_user_record(user.accountid, 
                              write_root_access=write_root_access) + '\n'
            record = record + '\n'

    if add_additional_users:
        if os.path.exists(settings.ADDITIONAL_LDAP_USER_FILE):
            f = open(settings.ADDITIONAL_LDAP_USER_FILE, "r")
            
            additional_users = ''

            if write_root_access:        
                additional_users = f.read()
            else:
                for line in f:
                    if (line.find('rootAccessGroup') == -1):
                        additional_users += line
 
            f.close()
            record = record + additional_users    

    return record    
    
    
                         
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
       if not user.accountid in EXCLUDE_USERS:
           record = record + 'memberUid: ' + user.jasminaccountid + '\n'
  
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
       if not user.accountid in EXCLUDE_USERS:
           accounts.append(user.jasminaccountid)
       
    accounts = accounts + ARCHIVE_ACCESS_STANDARD_USERS
#
#   Remove any duplicates
#
    accounts = list(set(accounts))
    
    for account in sorted(accounts):
       record = record + 'memberUid: ' + account + '\n'

    record = record + 'memberUid: bodc\n'
#    record = record + 'memberUid: train001\n'
#
#   Temporary modification only - add training accounts to open group
#
    for x in range (1,51):
        record = record + 'memberUid: train%03d\n' % x
    

    return record   

def ldap_archive_access_group_record(datasetid):

    record = ''
    
    if not datasetid in list(ARCHIVE_ACCESS_GROUPS.keys()):
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
        if not user.accountid in EXCLUDE_USERS:
            accounts.append(user.jasminaccountid)
        
    accounts = accounts  + ARCHIVE_ACCESS_STANDARD_USERS
#
#   Remove any duplicates
#
    accounts = list(set(accounts))
    
    for account in accounts:
        record = record + 'memberUid: ' + account + '\n'
         
    return record  

def ldap_user_tags(user):

    record = ''
#
#   Don't write any tags if account is not valid. This should already be
#   sorted in the userdb, but I have added this check just to make sure...
#
    if not is_ldap_user(user):
        return record + 'description: cluster:EX-login\n'
    
    if user.isJasminCemsUser():
        record = record + 'description: cluster:lotus\n'

    if user.hasDataset("system-login") or user.isJasminCemsUser():
        record = record + 'description: cluster:ceda-external\n'

    datasetjoins = user.currentDatasets(filter_duplicates=True)
    

    for datasetjoin in datasetjoins:
#
#      Wrap the following in try-except block as it has been known for
#      the foreign key integrity in the userdb to be broken...
#
       try:
           if datasetjoin.datasetid.grp.startswith('cluster:'):
               record = record + 'description: %s\n' % datasetjoin.datasetid.grp
           elif datasetjoin.datasetid.datasetid.startswith('vm_access_'):
               grp = datasetjoin.datasetid.grp
               if grp.strip():
                   record = record + 'description: %s\n' % datasetjoin.datasetid.grp       
                      
       except:
           pass 

    return record
    
        
def ldap_user_record(accountid, write_root_access=True):
    '''Returns LDAP record for given user'''
    
    
    record = ''
    
    try:
        user = User.objects.get(accountid=accountid)
    except:
        return "%s not found" % accountid
            
#    if not is_ldap_user (user):
#        return 'Not LDAP user'
    
#    if not user.uid > 0:
#        return 'uid not set for %s' % accountid
    
    record = "dn: cn=%s,ou=jasmin,ou=People,o=hpc,dc=rl,dc=ac,dc=uk\n" % user.accountid.strip()    
    record = record + 'loginShell: %s\n' % user_shell(user).strip()

    surname = user.surname.strip()
    
    if not surname:
        surname = 'Not specified'
    record = record + 'sn: %s\n' % surname

    record = record + 'objectClass: top\n'
    record = record + 'objectClass: person\n'
    
    record = record + 'objectClass: posixAccount\n'
    record = record + 'objectClass: ldapPublicKey\n'

    if write_root_access:
        record = record + 'objectClass: rootAccessGroup\n'
    
    record = record + 'gidNumber: %s\n' % user_gid(user)
    record = record + 'uid: %s\n' % user.accountid.strip()
    record = record + 'gecos: %s\n' % user_gecos(user).strip()   
    record = record + 'uidNumber: %s\n' % user.uid      
    record = record + 'cn: %s\n' % user.accountid.strip()
    
    record = record + ldap_user_tags(user)

    if write_root_access:
        record = record + 'rootAccessGroupName: NON-STAFF\n'
    
    record = record + 'homeDirectory: %s\n' % user_home_directory(user)
    
    record = record + 'sshPublicKey:'

    if not is_ldap_user (user):
         pass
#        record = record + ' ' + 'Account_inactive'
    else:
        if user.public_key.strip():
            record = record + ' ' + user.public_key.strip()
    record = record + '\n'
#
#   Sort records alphabetically then add dn at top
#                
#    record = '\n'.join(sorted(record.split('\n')))


    return record   
    
def ldif_all_groups (add_additions_file=True):
    """
    Returns all group information from the userdb as a sorted LDIF file
    Returns a filehandle for an open temporary file that can be read from.
    """
    a = tempfile.NamedTemporaryFile(mode='w+t', delete=True)
    record = ldap_all_group_records(add_additions_file=add_additions_file)
    a.write(record)
    a.flush()
     
    bb = tempfile.NamedTemporaryFile(delete=True)
    p2 = subprocess.Popen([LDAP.SORT_SCRIPT, "-a", "-k", "dn", a.name], stdout=bb)
    p2.wait()
            
    return bb

def ldif_all_group_updates (server=settings.LDAP_URL, select_groups=[], add_additions_file=True):
    """
    Returns ldiff commands to update LDAP group server as string array
    """
    
    server_ldif = LDAP.ldif_all_groups(filter_scarf_users=True, server=server, select_groups=select_groups)  
    
    udb_ldif = ldif_all_groups(add_additions_file=add_additions_file)
                		
    tmp_out = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/ldifdiff.pl"
    p1 = subprocess.Popen([script, "-k", "dn", "--sharedattrs", 
                            "memberUid", udb_ldif.name, server_ldif.name], stdout=tmp_out)
    p1.wait()
    
    tmp_out2 = open(tmp_out.name, 'r')
    diffoutput = tmp_out2.readlines()

    stringout = ""

    i = 0
    
    while i < len(diffoutput):
        stringout += diffoutput[i]        
        i = i + 1
    return stringout

def ldif_all_user_updates(server=settings.LDAP_URL):
    """
    Returns ldiff commands to update LDAP user server as string array
    """

    ldif = LDAP.ldif_all_users(server=server,filter_root_users=True)                  
    udb_ldif = ldif_all_users(write_root_access=False)

    d = tempfile.NamedTemporaryFile()
    script = settings.PROJECT_DIR + "/udbadmin/ldifdiff.pl"
    p1 = subprocess.Popen([script, "-k", "dn", "--sharedattrs", "description",  "--sharedattrs", "objectClass",
                       udb_ldif.name, ldif.name], stdout=d)
    p1.wait()
    #
    #       Read the output and convert into a string
    #    
    e = open(d.name, 'r')
    out = e.readlines()
    stringout = ""

    i = 0
    
    while i < len(out):
        if out[i].find('rootAccessGroup') == -1:

            if i< len(out)-1 and out[i+1].startswith('changetype: delete'):
                if out[i].startswith('dn: cn=aharwood') or out[i].startswith('dn: cn=xxxx'):
                    i = i + 1
                else:
                     stringout += out[i]
            else:
                stringout += out[i]
                
        i = i + 1
    
    return stringout
    
def ldif_all_users (write_root_access=True):
    """
    Returns all user information from the userdb as a sorted LDIF file
    Returns a filehandle for an open temporary file that can be read from.
    """
    a = tempfile.NamedTemporaryFile()
    record = ldap_all_user_records(write_root_access=write_root_access)

    a.write(record)
#    a.write(record.encode('utf8'))
    a.flush()
         
    bb = tempfile.NamedTemporaryFile()
    p2 = subprocess.Popen([LDAP.SORT_SCRIPT, "-a", "-k", "dn", a.name], stdout=bb)
    p2.wait()
            
    return bb
                
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
#
#      Temporary fix for user ttoniazzo to get around problem of NIS not handling long group lines. 
#    
    record = 'open:*:' + str(OPEN_GID) + ':' + 'spepler,ttoniazzo,' + \
          userAccountsString(users, extraAccounts=ARCHIVE_ACCESS_STANDARD_USERS)
#
#      Trim the record to 1024 characters. This is due to a lilmitation in the NIS system
#          
    record = record[0:1023]
    loc = record.rfind(',')
    record = record[0:loc]
          
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

    for accessGroup in list(ARCHIVE_ACCESS_GROUPS.keys()):            
        users = get_dataset_users(ARCHIVE_ACCESS_GROUPS[accessGroup]["datasets"])
        accountsString = userAccountsString(users, extraAccounts=ARCHIVE_ACCESS_STANDARD_USERS)
        record = record + accessGroup + ':*:' + str(ARCHIVE_ACCESS_GROUPS[accessGroup]["gid"]) + ':' + accountsString + "\n";
#
#      Generate 'open' data access group
#

    record = record + open_group_string()
   
    return record
       

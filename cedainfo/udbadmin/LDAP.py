import ldap
import os
import tempfile
import subprocess
from operator import itemgetter

from django.conf import settings

EXCLUDE_USERS = ['aharwood', 'mpryor', 'gparton', 'gpp02', 'mpritcha', 'wtucker', 'rsmith013', 'pjkersha', 'fchami', 'mattp', 'dch1fc']
#EXCLUDE_USERS = []

GROUP_BASE  = "ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"
PEOPLE_BASE = "ou=jasmin,ou=People,o=hpc,dc=rl,dc=ac,dc=uk"

SORT_SCRIPT = settings.PROJECT_DIR + '/udbadmin/ldifsort.pl'

l = ldap.ldapobject.ReconnectLDAPObject(settings.LDAP_URL, trace_level=0, retry_max=3)

def ceda_groups():

    """Returns all ceda group names"""
    
    groups = []
    
    try:
        results = l.search_s(GROUP_BASE, ldap.SCOPE_ONELEVEL)

        for dn, entry in results:
           if 'cluster:ceda-external' in entry['description']:
              entry['external'] = True
           else:
              entry['external'] = False
                 
           if 'cluster:ceda-internal' in entry['description']:
              entry['internal'] = True
           else:
              entry['internal'] = False
                 
           groups.append(entry)

        groups = sorted(groups, key=itemgetter('cn'))          
    except:
        pass
        
    return groups
        

def group_members (group):

    """Returns members of given group"""
    
    try:
        base = "cn=%s," % group + GROUP_BASE
        (dn, entry) = l.search_s(base , ldap.SCOPE_BASE)[0]
        return entry['memberUid']
    except:
        return []

def member_groups (accountID):
#
#      Returns groups that the given member belongs to
#    
    groups = []
    
    try:
        base = GROUP_BASE
        results = l.search_s(base , ldap.SCOPE_SUBTREE, 'memberUid=%s' % accountID)
         
        for dn, entry in results:
           groups.append(entry)
    except:
        pass
        
    return groups    


def group_details (group):
#
#      Returns details of given group
#    
    try:
        base = "cn=%s," % group + GROUP_BASE
        (dn, entry) = l.search_s(base , ldap.SCOPE_BASE)[0]
 
        if entry.has_key('memberUid'):       
           entry['memberUid'] = sorted(entry['memberUid'])

        return entry
    except:
        return []

def peopleTags ():

    """Returns list of description tags used for people"""

    return personAttributeValues('description')        

def rootAccessGroupNameValues():
    """Returns list of values used for the 'rootAccessGroupName' attribute"""
    return personAttributeValues('rootAccessGroupName')
    
def personAttributeValues (attribute):

    """Returns all values of the given attribute"""
        
    base = PEOPLE_BASE
    
    results = l.search_s(base , ldap.SCOPE_ONELEVEL, attrlist=[attribute])

    tags = []

    for dn, entry in results:
        if entry:
            tags = tags + entry[attribute]

    tags = list(set(tags))
    tags.sort()  
    return tags


def groupTags ():

    """Returns list of tags used for groups"""
        
    base = GROUP_BASE
    results = l.search_s(base , ldap.SCOPE_ONELEVEL, attrlist=['description'])

    tags = []

    for dn, entry in results:
        if entry:
            tags = tags + entry['description']

    tags = list(set(tags))
    tags.sort()  
    return tags
        

def tag_members (tagName):
#
#      Returns membses with the given tag. If no tag is given then returns all users
#    
    users = []

        
    try:
        base = PEOPLE_BASE
        
        if tagName:
            results = l.search_s(base , ldap.SCOPE_ONELEVEL, 'description=%s' % tagName)
        else:
            results = l.search_s(base , ldap.SCOPE_ONELEVEL)

        for dn, entry in results:
            users.append(entry)
        
        users = sorted(users, key=itemgetter('uid'))
    except:
        pass
         
    return users   


def attribute_members (attributeName, attributeValue):
    """Returns members who have the given attribute set to the given value"""
    
    users = []
        
    try:
        base = PEOPLE_BASE
        

        results = l.search_s(base , ldap.SCOPE_ONELEVEL, '%s=%s' % (attributeName, attributeValue))

        for dn, entry in results:
            users.append(entry)
        
        users = sorted(users, key=itemgetter('uid'))
    except:
        pass
         
    return users   


def member_details (uid):

    """Returns details for member with given uid (accountid)"""    

    base = PEOPLE_BASE
    
    try:    
        userDetails = l.search_s(base , ldap.SCOPE_ONELEVEL, 'uid=%s' % uid) 
    except:
        pass
         
    return userDetails[0][1]

def all_member_details ():
    """Returns details for all members"""
    
    base = PEOPLE_BASE
    
    try:    
        userDetails = l.search_s(base , ldap.SCOPE_ONELEVEL) 
    except:
        pass
         
    return userDetails

def all_member_accountids ():
    """Returns list of all accountid values in LDAP database"""

    ldap_member_details = all_member_details()

    accountids = []

    for member in ldap_member_details:
        accountids.append(member[1]['uid'][0])

    return accountids

def peopleTagChoices():
    """Returns peopleTags as list suitable for use as 'choices' argument in forms"""
    
    tags = peopleTags()

    choices = [('', 'All users')]
    
    for tag in tags:
       choices.append ((tag, tag))

    return choices


def rootAccessMembers():
    """Returns list of accountIDs of members who have root access privilege"""
    memberAccounts = []
    
    groupNames = rootAccessGroupNameValues()

    for name in groupNames:
#
#              Ignore values of rootAccessGroupName that are not actually used
#    
        if not (name == 'NON-STAFF' or name == 'NON_STAFF'):
            members = attribute_members('rootAccessGroupName', name)
 
            for member in members:
                memberAccounts.append(member['uid'][0])

    memberAccounts = list(set(memberAccounts))
    memberAccounts .sort()
    
    return memberAccounts


def ldif_all_groups (filter_scarf_users=False, server=settings.LDAP_URL, select_groups=[]):
    """
    Returns all LDIF information from LDAP server for ceda groups, sorted by dn.
    Returns a filehandle for an open temporary file that can be read from.
    
    select_groups can be used to select only the specified groups

    if filter_scarf_users is set then scarf users are removed from the output 
    using grep.
    """
    group_filter = _get_ldap_group_filter_string (select_groups)

#    print group_filter
#    group_filter = "(|(cn=ukmo)(cn=ecmwf)(cn=cmip5_research)(cn=esacat1)(cn=eurosat)(cn=ukmo_wx)(cn=ukmo_clim)(cn=open))"
#    group_filter='(cn=gws_nceo_generic)'
#    group_filter = '(cn=*)'

    b = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ldapsearch", "-LLL",  "-x", "-H", server, "-b", GROUP_BASE, "-s", "one", group_filter], stdout=b)
    p1.wait()

    bb = tempfile.NamedTemporaryFile()

    if filter_scarf_users:
	cc = tempfile.NamedTemporaryFile()
	
        p2 = subprocess.Popen([SORT_SCRIPT, "-a", "-k", "dn", b.name], stdout=cc)
        p2.wait()

	grep_string = "memberUid: scarf"

	for entry in EXCLUDE_USERS:
	    grep_string = grep_string + "|memberUid: %s$" % entry

	ccin = open(cc.name, 'r')
        p3 = subprocess.Popen(["egrep", "-v", grep_string], stdin=ccin, stdout=bb)
        p3.wait() 

    else:
        p2 = subprocess.Popen([SORT_SCRIPT, "-a", "-k", "dn", b.name], stdout=bb)
        p2.wait()
  
    return bb

def _get_ldap_group_filter_string (groups=[]):
    """
    Returns the filter string that can be used with ldapsearch to select only the given groups from
    the LDAP server. If no groups are specified then wildcard selection string is returned 
    (to select all groups)
    """

    if len(groups) == 1:
            group_filter = '(cn=%s)' % groups[0]
    elif len(groups) > 1:
    	    group_filter = '(|'

            for group in groups:
	        group_filter += '(cn=%s)' % group    
            group_filter += ')'		

    else:
	group_filter = '(cn=*)'

    return group_filter

def ldif_all_users (filter_root_users=False, server=settings.LDAP_URL):
    """
    Returns all LDIF information from LDAP server for ceda users, sorted by dn.
    Returns a filehandle for an open temporary file that can be read from.

    NB I found that using stdout=subprocess.PIPE did not work when callling the
    sort script, so I had to create temporary files for piping output between 
    commands.

    """
    b = tempfile.NamedTemporaryFile()
#
#   Filter to exclude any users whose details we don't want
#   
    filter_string = "(!(|(uid=dummEntry)"  

    for entry in EXCLUDE_USERS:
	filter_string += "(uid=%s)" % entry
    filter_string += "))"	

    p1 = subprocess.Popen(["ldapsearch", "-LLL",  "-x", "-H", server, "-b", PEOPLE_BASE, "-s", "one", filter_string], stdout=b)
    p1.wait()

    bb = tempfile.NamedTemporaryFile()

    if filter_root_users:
        cc = tempfile.NamedTemporaryFile()

        p2 = subprocess.Popen([SORT_SCRIPT, "-a", "-k", "dn", b.name], stdout=cc)
        p2.wait()

        ccin = open(cc.name, 'r')
#        p3 = subprocess.Popen(["grep", "-v", "rootAccessGroup"], stdin=ccin, stdout=bb)
        p3 = subprocess.Popen(["egrep", "-v", "rootAccessGroup|userPassword"], stdin=ccin, stdout=bb)
        p3.wait() 
 
    else:
        p2 = subprocess.Popen([SORT_SCRIPT, "-a", "-k", "dn", b.name], stdout=bb)
        p2.wait()
        
    return bb

def ldif_user (uid, server=settings.LDAP_URL):
    """
    Returns all LDIF information from LDAP server the given uid
    """
    b = tempfile.NamedTemporaryFile()
   
    p1 = subprocess.Popen(["ldapsearch", "-LLL",  "-x", "-H", server, "-b", PEOPLE_BASE, 
                            "-s", "one", "(uidNumber=%s)" % uid], stdout=b)
    p1.wait()

    bb = tempfile.NamedTemporaryFile(delete=True)

    p2 = subprocess.Popen([SORT_SCRIPT, "-a", "-k", "dn", b.name], stdout=bb)
    p2.wait()
        
    return bb


def ldif_write (ldif, server=settings.LDAP_WRITE_URL):
    """
    Write the given ldif commands to the ldif server
    """

#
#   Write ldif commands to a temporary file
#
    output = tempfile.NamedTemporaryFile()
       
    ldif = ldif.replace('\r', '')

    (fh, input_file_name) = tempfile.mkstemp()

    os.write(fh, ldif)
    os.close(fh)
#
#   Call ldapmodify and read input from temporary file
#    
    tmp2 = open(input_file_name, 'r')
    
    p1 = subprocess.Popen(["ldapmodify", "-ZZZ", "-H", server, "-D", 
                            settings.LDAP_WRITE_DN, 
                            "-w", settings.LDAP_WRITE_PASSWD], stdin=tmp2, stdout=output, stderr=output)
    p1.wait()

    os.remove(input_file_name)
    
    tmp3 = open(output.name, 'r')
    stdout = tmp3.readlines()
            
    return stdout


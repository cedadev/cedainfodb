import ldap
import tempfile
import subprocess
from operator import itemgetter

LDAP_URL    = 'ldap://homer.esc.rl.ac.uk'
GROUP_BASE  = "ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"
PEOPLE_BASE = "ou=ceda,ou=People,o=hpc,dc=rl,dc=ac,dc=uk"

#l = ldap.initialize(LDAP_URL)
l = ldap.ldapobject.ReconnectLDAPObject(LDAP_URL, trace_level=0, retry_max=3)

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
#      Returns groups that the fiven member belongs to
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

    """Returns members with the given tag. If no tag is given then returns all users"""    

    base = PEOPLE_BASE
    
    try:    
        userDetails = l.search_s(base , ldap.SCOPE_ONELEVEL, 'uid=%s' % uid) 
    except:
        pass
         
    return userDetails[0][1]


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


def ldif_all_groups ():
    """
    Returns all LDIF information from LDAP server for ceda groups, sorted by dn.
    Returns a filehandle for an open temporary file that can be read from.
    """
    
    b = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ldapsearch", "-LLL",  "-x", "-H", LDAP_URL, "-b", GROUP_BASE, "-s", "one"], stdout=b)
    p1.wait()

    bb = tempfile.NamedTemporaryFile()
    script = "/home/badc/software/infrastructure/cedainfo_releases/current/cedainfo/udbadmin/ldifsort.pl"
    p2 = subprocess.Popen([script, "-a", "-k", "dn", b.name], stdout=bb)

    p2.wait()
            
    return bb

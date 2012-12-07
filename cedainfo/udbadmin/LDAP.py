import ldap

from operator import itemgetter


LDAP_URL    = 'ldap://homer.esc.rl.ac.uk'
GROUP_BASE  = "ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"
PEOPLE_BASE = "ou=ceda,ou=People,o=hpc,dc=rl,dc=ac,dc=uk"

l = ldap.initialize(LDAP_URL)



def ceda_groups():
#
#      Returns all ceda group names
#
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
#
#      Returns membses of given group
#    
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


def member_details (uid):
#
#      Returns membses with the given tag. If no tag is given then returns all users
#    

    base = PEOPLE_BASE
    
    try:    
        userDetails = l.search_s(base , ldap.SCOPE_ONELEVEL, 'uid=%s' % uid) 
    except:
        pass
         
    return userDetails[0][1]

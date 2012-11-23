import ldap


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
           groups.append(entry['cn'][0])
           
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


def cluster_members (clusterName):
#
#      Returns membses of given 'cluster'
#    
    users = []
    
    try:
        base = PEOPLE_BASE
        results = l.search_s(base , ldap.SCOPE_ONELEVEL, 'description=cluster:%s' % clusterName)
 
        for dn, entry in results:
           users.append(entry['uid'][0])

        users.sort()  
    except:
        pass
         
    return users   

                 
users = cluster_members('jasmin-login')

for user in users:
   print user
   
#groups = ceda_groups()
#groups.sort()
#
#for group in groups:
#   if group.startswith('gws_') or group == 'upscale':
#      print group
#      members = group_members(group)
#      members.sort()
#      for member in members:
#          print ' ', member
      
      
#members = group_members('gws_pagoda')
#for member in members:
#   print member
#for dn,entry in r:
#   print 'Processing', repr(dn)
#   print entry
#   try:
#      print entry['memberUid']
#   except:
#       pass

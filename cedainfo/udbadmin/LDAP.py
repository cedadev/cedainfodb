import ldap


LDAP_URL   = 'ldap://homer.esc.rl.ac.uk'
GROUP_BASE = "ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"

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


                 

groups = ceda_groups()
groups.sort()

for group in groups:
   if group.startswith('gws_'):
      print group
      members = group_members(group)
      for member in members:
          print ' ', member
      
      
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

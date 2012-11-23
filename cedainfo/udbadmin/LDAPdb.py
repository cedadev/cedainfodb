from subprocess import *

SERVER     = "ldap://homer.esc.rl.ac.uk"
BASE       = "ou=People,o=hpc,dc=rl,dc=ac,dc=uk"
CMD        = "/usr/bin/ldapsearch"
TAG_PREFIX = "description: cluster:"

class LDAPdb:
    '''
    Class for reading information from LDAP database which is used for JASMIN/CEMS accounts
    '''       
    
    def tags(self):
        '''
        Returns list of relevant LDAP tag names
        '''
        
        tags = []
        
        p1 = Popen([CMD, "-L", "-x", "-H %s" % SERVER, "-b %s" % BASE, '(description=cluster:*)'], stdout=PIPE)
        p2 = Popen(["grep",  '^%s' % TAG_PREFIX], stdin=p1.stdout, stdout=PIPE)
        p3 = Popen(["sort", "-u"], stdin=p2.stdout, stdout=PIPE)
        out = p3.communicate()[0]
        
        for line in out.split('\n'):
            line = line.replace(TAG_PREFIX, '')
            if line: tags.append(line)

        return tags

        
    def members(self, tag, uid=False):
        '''
        Returns list of members for the given tag. By default returns their accountid, but if uid=True it 
        returns uid numbers (as list of strings)
        '''
    
        results = []
        
        if uid:
            prefix = 'uidNumber: '
        else:
            prefix = 'uid: '
           
        p1 = Popen([CMD, "-L", "-x", "-H %s" % SERVER, "-b %s" % BASE, '(description=cluster:%s)' % tag], stdout=PIPE)
        p2 = Popen(["grep",  '^%s' % prefix], stdin=p1.stdout, stdout=PIPE)
        p3 = Popen(["sort", "-u"], stdin=p2.stdout, stdout=PIPE)
        out = p3.communicate()[0]
        
        for line in out.split('\n'):
            line = line.replace(prefix, '')
            if line: results.append(line)

        return results
        
a = LDAPdb()
print a.members('jasmin-login', uid=True)

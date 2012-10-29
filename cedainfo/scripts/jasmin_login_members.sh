#
# Use ldapsearch to list members of jasmin-login
#
ldapsearch -LL -x -H ldap://homer.esc.rl.ac.uk -b "ou=ceda,ou=People,o=hpc,dc=rl,dc=ac,dc=uk"  "(description=cluster:jasmin-login)"  uid |grep 'uid:' | cut -d' ' -f2 |sort

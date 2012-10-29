#
# Lists all LDAP groups. If a group name is given then lists group membership
#

if [ $# -ne 1 ]
then
   ldapsearch -LL -x -H ldap://homer.esc.rl.ac.uk -b "ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk" |grep 'cn:' |sort |cut -d' ' -f2
else
   ldapsearch -LL -x -H ldap://homer.esc.rl.ac.uk -b "cn=$1,ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"  |grep 'memberUid:'|cut -d' ' -f2|sort
fi   

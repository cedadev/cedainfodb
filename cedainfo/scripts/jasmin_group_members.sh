#
# Use ldapsearch to list members of given group. If no group is specified then list all members of all groups
#

if [ $# -ne 1 ]
then
   ldapsearch -LLL -x -H ldap://homer.esc.rl.ac.uk -b "ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk" dn memberUid
else
   echo "Group: $1"
   ldapsearch -LL -x -H ldap://homer.esc.rl.ac.uk -b "cn=$1,ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"  |grep 'memberUid:'|cut -d' ' -f2|sort
fi

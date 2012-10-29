#
# Use ldapsearch to list members of given group
#
echo "Group: $1"
ldapsearch -LL -x -H ldap://homer.esc.rl.ac.uk -b "cn=$1,ou=ceda,ou=Groups,o=hpc,dc=rl,dc=ac,dc=uk"  |grep 'memberUid:'|cut -d' ' -f2|sort

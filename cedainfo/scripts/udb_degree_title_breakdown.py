#
# Generates breakdown of users 'Title' by 'Degree type' for 'active' users.
# 'Active' users have at least one current dataset. The output from this program
# can be piped through sort and then "uniq -c" to generate the final stats.
#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript udb_degree_title_breakdown
#
  
from udbadmin.models import *

def run():
   
   users = User.objects.all()
   
   for user in users:
      if user.datasetCount() > 0: 
       
         if not user.degree: 
            degree = 'None'
         else:
            degree = user.degree
               
         print("%s:%s" % (degree, user.title))

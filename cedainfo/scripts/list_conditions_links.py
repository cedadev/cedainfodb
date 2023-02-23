#
# This script is intended to be run via the 'runscript' option of manage.py:
#
#    python manage.py runscript <script-name-without-py-extension>
#
#
#
import sys
import requests, urllib
from udbadmin.models import *


def run():


    datasets = Dataset.objects.all()
    
    for dataset in datasets:
    
       if not dataset.conditions.strip():
           continue
 
##       if dataset.authtype in ("none"):
            
       if dataset.authtype not in ("none", "jasmin-portal"):
          conditions = dataset.conditions

          conditions = conditions.replace("$HTDOCS", "$HTROOT")
          
          if "$HTROOT"  in conditions:
             conditions = conditions.replace("$HTROOT/conditions", "http://licences.ceda.ac.uk/image/data_access_condition")
             conditions = conditions.replace("$HTROOT/data", "http://licences.ceda.ac.uk/image/data_access_condition")

             conditions = conditions.replace(".html", ".pdf")
             response = requests.head(conditions)
             
             if response.status_code == 200:	     
                print (dataset.datasetid, conditions)
             else:
                print ('ERROR', dataset.datasetid, response.status_code, conditions)
    
          elif "http" in conditions:
          
             print (dataset.datasetid, conditions)
#                response = requests.head(conditions)
#                
#                if response.status_code == 301:
#                    print ('CCC', dataset.datasetid, response.status_code, conditions)
#                else:
#                    print ('XXX', dataset.datasetid, response.status_code, conditions)
                

          else:
                print ('ERROR', dataset.datasetid, '"', conditions, '"')

#!/usr/bin/env python
'''
Example script showing use of django api to extract properties of a data entity.
Takes 1 command-line argument, the moles data entity id to be looked up.
'''
import sys
from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *

def get_dataentity(dataentity_id):
    '''
    Return a DataEntity object matching the supplied dataentity_id.
    Returns None if no matching object found
    Note that the dataentity_is the MOLES data entity id, and is distinct
    from the (internal) field "id" which is used by django as the primary key.
    '''
    try:
        dataentity = DataEntity.objects.get(dataentity_id=dataentity_id)
        return dataentity
    except:
        return None

if __name__=="__main__":
    dataentity_id=sys.argv[1]
    de = get_dataentity(dataentity_id)
    if de != None:
        print "DataEntity details:"
        print "id = %s" % de.id
	print "dataentity_id = %s" % de.dataentity_id
        print "symbolic_name = %s" % de.symbolic_name
	print "recipes_expression = %s" % de.recipes_expression
	print "recipes_expression = %s" % de.recipes_explanation
	print "recipes_expression = %s" % de.access_status
    else:
        print "No dataentity found with dataentity_id=\"%s\" does not exist" % dataentity_id


        
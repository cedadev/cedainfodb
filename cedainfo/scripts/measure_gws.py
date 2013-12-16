#
# Script to measure USED sizes of Group Workspaces
from cedainfoapp.models import GWS
import os

def measure(gws):
	dir = os.path.join(gws.path, gws.name)
	if os.path.isdir(dir):
		print "Measuring %s at %s" % (gws.name, dir)
		gws.pan_df()
	else:
		raise Exception("Directory does not exist: %s" % dir)
	
    

def run():
    for i in GWS.objects.all():
        try:
			measure(i)
        except Exception, e:
            print "Error measuring GWS",str(e)

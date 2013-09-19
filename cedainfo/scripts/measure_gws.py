#
# Script to measure USED sizes of Group Workspaces
from cedainfoapp.models import GWS

def measure(gws):
    print "Measuring %s" % gws.name
    

def run():
    for i in GWS.objects.all():
        measure(i)
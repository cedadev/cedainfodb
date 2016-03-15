#
# Script to update sizes of Group Workspaces en masse
from cedainfoapp.models import GWS

def update(filename):
    # open data file containing name of gws in first col, size in bytes in 2nd optional et_quota in third
    with open(filename, 'r') as f:
        data = f.readlines()

        for line in data:
            [name, vol] = line.split()
            print name
            g = GWS.objects.get(name=name)
            g.requested_volume = vol
            g.forceSave()

        
    

def run():
    # process list of GWSs from file

    update("gws_size_update.txt")

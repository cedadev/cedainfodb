# script to update all df info for partitions


from cedainfoapp.models import *

def do_dfs():
    # do df for all partitions
    partitions = Partition.objects.all()
    for p in partitions:
        print("Doing df of partition: %s " % p)
        p.df()  


def run ():
    do_dfs()

    

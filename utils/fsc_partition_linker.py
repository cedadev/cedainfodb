import sys
import os
import re

from django.core.management import setup_environ
import settings
setup_environ(settings)

from cedainfoapp.models import *

def parse_logical_path(path):
    '''Parse data centre name (e.g. neodc, badc) and dataset symbolic name from FileSetCollection logical_path e.g. /neodc/arsf'''
    p = re.compile(r'^/(badc|neodc)/(.*)/?$')
    match = p.match(path)
    data_centre_name = match.groups()[0]
    symbolic_name = match.groups()[1]
    return (data_centre_name, symbolic_name)

def get_top_level_dir(partition, prefix, symbolic_name):
    top_level_dir = os.path.join(partition.mountpoint, prefix, symbolic_name)
    return top_level_dir

def get_expansion_path_and_top_level_dir(partition, fsc_logical_path):
    '''Returns the expansion path (/disks/machineN/archive/NAME), given partition and /datacentre/NAME'''
    (data_centre_name, symbolic_name) = parse_logical_path(fsc_logical_path)

    # make directories in each partition
    top_level_dir = get_top_level_dir(partition, 'archive', symbolic_name)
    if partition.expansion_no == 0:
        expansion_path = fsc_logical_path
    else:
        # /neodc/.arsf_expansion1
        expansion_path = os.path.join('%s%s' % (os.path.sep, data_centre_name),'.%s_expansion%d' % (symbolic_name, partition.expansion_no) )
    return (expansion_path, top_level_dir)

class fsc_partition_linker:
    '''Links FileSetCollection to Paritions within a PartitionPool (physically).
       Author : Matt Pritchard 
    '''
    def __init__(self, path):
        self.logical_path = path
        self.fsc = FileSetCollection.objects.get(logical_path=self.logical_path)

    def link_fsc_to_partition(self):
        # Find the partitions belonging to the partitionpool of this FileSetCollection
        partitions = Partition.objects.filter(partition_pool=self.fsc.partitionpool)
        (data_centre_name, symbolic_name) = parse_logical_path(self.logical_path)
        for partition in partitions :
            
            # Create a directory on the partition
            # Create a symlink to that directory
            print '%s -> %s' % get_expansion_path_and_top_level_dir(partition, self.logical_path)

if __name__=="__main__":
    logical_path = sys.argv[1]
    linker = fsc_partition_linker(logical_path)
    linker.link_fsc_to_partition()

    
# Spec.
#logical path = /neodc/arsf (known from FileSetCollection)
#host = anticyclone
#partitions = (part of same partitionpool) (convention : partition names are /disks/hostnameN)
#  /disks/anticyclone1 (expansion_no = 0)
#  /disks/anticyclone2 (expansion_no = 1)
#
#filesetcollection = arsf
#...need to create:
#  /disks/anticyclone1/archive/arsf
#  /disks/anticyclone2/archive/arsf
#  symlink /neodc/arsf -> /disks/anticyclone1/archive/arsf (for expansion 0)
#  symlink /neodc/.arsf_expansion1 -> /disks/anticyclone2/archive/arsf (for expansion 1)
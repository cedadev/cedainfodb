import getopt, sys
import os, errno
import re
import logging
import csv

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

def mkdir_p(path):
    '''replicate mkdir -p behaviour'''
    try:
        os.makedirs(path)
    except OSError, e:
        if e.errno == errno.EEXIST:
            # If dir exists already, skip gracefully
            logging.warn( "Directory exists : %s : skipping" % path )
            pass
        else: raise

def ln(src, dst):
    '''make symlink or skip gracefully if this exists already'''
    try:
        os.symlink(src, dst)
    except OSError, e:
        if e.errno == errno.EEXIST:
            # If dir exists already, skip gracefully
            logging.warn( "Link exists : %s : skipping" % dst )
            pass
        else: raise


class fsc_partition_linker:
    '''Links FileSetCollection to Paritions within a PartitionPool (physically).
       Author : Matt Pritchard 
    '''
    def __init__(self, path):
        self.logical_path = path
        self.fsc = FileSetCollection.objects.get(logical_path=self.logical_path)

    def link_fsc_to_partitions(self):
        # Find the partitions belonging to the partitionpool of this FileSetCollection
        partitions = Partition.objects.filter(partition_pool=self.fsc.partitionpool)
        (data_centre_name, symbolic_name) = parse_logical_path(self.logical_path)
        for partition in partitions :
            (expansion_path, top_level_dir) = get_expansion_path_and_top_level_dir(partition, self.logical_path)
            # Create a directory on the partition (should skip if exists already)
            logging.info( 'Making dir %s' % top_level_dir )
            mkdir_p(top_level_dir)

            # Create a symlink to that directory (should skip if exists already)
            (expansion_link, top_level_dir) = get_expansion_path_and_top_level_dir(partition, self.logical_path)
            logging.info( '%s -> %s' % (top_level_dir, expansion_link) )
            # should be creating the link '/badc/.cmip5_expansionX' (dst), pointing to '/disks/lime1/archive/cmip5' (src)
            ln(top_level_dir, expansion_link)

class fsc_fileset_dir_maker:
    '''Makes FileSet dirs for all FileSets in a FileSetCollection (defined by logical path), and links
       them from top level dir'''
    def __init__(self, path):
        self.logical_path = path
        self.fsc = FileSetCollection.objects.get(logical_path=self.logical_path)
        
    def make_fileset_dirs(self):
        # Iterate through FileSetCollection Relations for this FileSetCollection
        fscrs = FileSetCollectionRelation.objects.filter(fileset_collection=self.fsc)
        # Construct the path to each fileset
        for fscr in fscrs:
            if fscr.is_primary:
                # logical path = path of filesetcollection + relative path of this fileset
                logical_path = os.path.join( self.fsc.logical_path, fscr.logical_path )
                # physical path = top_level_dir (on that partition) + relative path of this fileset
                # case 1: fileset on primary partition (expansion_no = 0)
                if fscr.fileset.partition is not None:
                    (expansion_path, top_level_dir) = get_expansion_path_and_top_level_dir(fscr.fileset.partition, self.fsc.logical_path)
                    physical_path = os.path.join(expansion_path, fscr.logical_path)
                    if fscr.fileset.partition.expansion_no == 0:
                        # make this dir
                        logging.info( "mkdir_p(%s)" % physical_path )
                        #mkdir_p(physical_path)
                        # no links to make in this case
                    elif fscr.fileset.partition.expansion_no > 0:
                        # To make the partent dir of the FileSet, first find the dir of the FileSet
                        fs_full_path = os.path.join( top_level_dir, fscr.logical_path )
                        # Now lop off the FileSet dir to get to the parent
                        (parent, fs) = os.path.split( fs_full_path )
                        # make the parent
                        logging.info( "mkdir_p(%s)" % parent )
                        #mkdir_p( parent )
                        # make the symlink (sits in the parent dir ...ie. = fs_full_path) pointing to the expansion dir
                        logging.info( "ln(%s, %s)" % (physical_path, fs_full_path) )
                        #ln( physical_path , fs_full_path )
                    else:
                        logging.error( "Invalid expansion no for partition %s" % fscr.fileset.partition )
                else:
                        logging.error( "No partition allocated for fileset : unable to make & link fileset dirs" )
                        pass
            else:
                pass
                # TODO work out what to do for secondary FileSetCollectionRelations

def fileset_will_fit(fileset, partition, threshold=0.9):
    '''Check to see if a fileset will fit on available space on partition'''
    # Find out how much space is available on a partition (from capacity_bytes & current allocations)
    partition.available_space = partition.capacity_bytes # to start with
    # find the FileSets current allocates to this partition
    partition.filesets = FileSet.objects.filter(partition=partition)
    for allocated_fileset in partition.filesets:
        partition.available_space = partition.available_space - allocated_fileset.overall_final_size
    
    result = None
    if fileset.overall_final_size <= (partition.available_space * threshold):
        result = True
        logging.info( "FileSet: %d\tAvailable:\t%d\tResult:\t%d" % (fileset.overall_final_size, (partition.available_space * threshold), result) )
    else:
        result = False
        logging.info( "FileSet: %d\tAvailable:\t%d\tResult:\t%d" % (fileset.overall_final_size, (partition.available_space * threshold), result) )

    return result
    
        
    

class allocator:
    '''Allocates filesets in a FileSetCollection to partitions in the associated partitionpool'''
    def __init__(self, path):
        self.logical_path = path
        self.fsc = FileSetCollection.objects.get(logical_path=self.logical_path)

    def allocate_round_robin(self):
        # get the list of FileSets to allocate, in reverse order of size (...= fscr.fileset.overall_final_size)
        # TODO ...find a less hacky way of doing this (hardcodes table name cedainfoapp_fileset)
        fscrs = FileSetCollectionRelation.objects.filter(fileset_collection=self.fsc).select_related(depth=1).order_by('-cedainfoapp_fileset.overall_final_size')
        filesets = []
        i=0
        for fscr in fscrs:
            filesets.append(fscr.fileset)
            # make a note of is_primary ...means we can handle things in one go later
            filesets[i].is_primary = fscr.is_primary
            if (filesets[i].is_primary):
                filesets[i].relative_logical_path = fscr.logical_path
            i += 1


        # get all the partitions that belong to this PartitionPool (...that is associated with this FileSetCollection)
        # And filter them by a computed field ie capacity - used = available
        partitions_qs = Partition.objects.filter(partition_pool=self.fsc.partitionpool).extra(select={ 'avail' : 'capacity_bytes - used_bytes'}).extra(order_by=['-avail'])
        # make a list of these (easier to work with)
        partitions = []
        for p in partitions_qs:
            partitions.append(p)
 
        # Go through FileSets in order, allocating to the partition next in the list, then sending that partition to the bottom of the list to be reused later        

        for fs in filesets:
            
            # check to see if this FileSetCollectionRelation is primary
            if fs.is_primary:
                # check to see if FileSet already has a partition allocated
                if fs.partition is None:
                    alloc_partition = partitions.pop(0)
                    # TODO ...test if the FileSet's total overall size will fit on this partition
                    # algorithm : yes if fileset.overall_final_size <= threshold * partition.available_space
                    #               where partition.available_bytes = capacity_bytes - (sum of all filesets' overall final sizes)
                    if fileset_will_fit(fs, alloc_partition):
                        logging.info("FileSet %s will fit on partition %s" % (fs, alloc_partition.mountpoint) )                       
                        fs.partition = alloc_partition

                        logging.debug("Saved changes to FileSet %s" % fs)
                        # Make the directories down to this FileSet dir
                        fileset_path = os.path.join(self.fsc.logical_path, fs.relative_logical_path)
                        logging.debug("FileSet path to make = %s" % fileset_path)
                        mkdir_p(fileset_path)
                        fs.save()
                    else:
                        logging.warn("FileSet %s won't fit on partition %s" % (fs, alloc_partition.mountpoint) )
                        # skip this partition ...try the next
                        pass
                    # TODO ...update this partition's availability value to reflect the fact we've just given it a load of data (but not really, yet)

                    partitions.append( alloc_partition )
                else:
                    logging.warn( "FileSet %s already allocated to Partition %s" % (fs, fs.partition.mountpoint) )
            else:
                logging.error( "Handling non-primary FileSetCollectionRelations not implemented yet" )

class filesetmaker:
    '''Allocates filesets in a FileSetCollection to partitions in the associated partitionpool'''
    def __init__(self, path):
        self.logical_path = path
        self.fsc = FileSetCollection.objects.get(logical_path=self.logical_path)
        
    def make_filesets_from_csv(self, csvfile):  # NB csvfile = file object (not filename)
        logging.info("Make filesets from CSV file")
        try:
            csvReader = csv.reader(csvfile, delimiter=',')
            logging.debug("Opened CSV file %s" % csvfile) 
        except(IOError), e:
            logging.error("Could not open CSV file %s : exiting\n" % csvfile )
            pass

        try:
            fsc = FileSetCollection.objects.get(logical_path=self.logical_path)
            logging.debug("Here: Found FileSetCollection %s" % fsc)
            fscr_made = []
            #size_column = fsc_manager_csv_cols['size']
            size_column = 6
            logging.debug("Size column: %d" % size_column)
            #path_column = fsc_manager_csv_cols['path']
            path_column = 7
            logging.debug("Path column: %d" % path_column)

            for row in csvReader:
                #TODO : skip if FileSet already exists with this relative path in this FSC
                if ((row[path_column] is not None) and (row[path_column] != "")):
                    (requested_vol,FileSet_relative_logical_path) = (int(row[size_column]),row[path_column])
                    # check first to see if FileSet already exists with this relative path
                    fscr_existing = FileSetCollectionRelation.objects.filter(fileset_collection=fsc).filter(logical_path=FileSet_relative_logical_path)
                    if (fscr_existing.count() == 0):
                        logging.info("Creating FileSet:  %s : %s" % (FileSet_relative_logical_path, requested_vol) )
                        fs = FileSet(overall_final_size=requested_vol)
                        logging.debug("Created FileSet")
                        fs.save()
                        logging.debug( "FileSet %s OverallFinalSize %s" % (fs, fs.overall_final_size) )
                        fscr = FileSetCollectionRelation(fileset=fs, fileset_collection=fsc, logical_path=FileSet_relative_logical_path, is_primary=True)
                        logging.debug( "FSCR %s Label %s" % (fscr, fs.label) )
                        fscr.save() # save method should re-save fs so don't need to explicitly do fs.save() again
                        fscr_made.append(fscr)
                        logging.info( "Created FSCR %s Label %s" % (fscr, fs.label) )
                    else:
                        logging.warn("FileSet with this logical path already exists : " % FileSet_relative_logical_path)
                else:
                    logging.warn( "Insufficient info : %s" % row )
                    pass        
        except:
            logging.error("Error processing FileSetCollection %s : exiting" % self.logical_path)
            
        # return a list of the filesetcollectionrelations created
        return fscr_made

def usage():
    print "FileSetCollection Manager"
    print "Usage: %s <arguments>" % sys.argv[0]
    print "Arguments:"
    print "\t-a --action"
    print "\t\tlink_fsc_partitions:"
    print "\t\t\tLink FileSetCollection to Partitions in PartitionPool"
    print "\t\tallocate"
    print "\t\t\tMake FileSets"
    print "\t\tmake_filesets"
    print "\t\t\tAllocate Partitions to FileSets"
    print "\t\tmake_fsdirs"
    print "\t\t\tMake and link directories for FileSets"
    print "\t-p --path"
    print "\t\tlogical path of FileSetCollection to be managed"
    print "\t-c --csvfile"
    print "\t\tCSV File (for action=make_filesets)"


    

def main():
    logging.basicConfig(level=logging.INFO)

    try:
        opts, args = getopt.getopt(sys.argv[1:], "ha:p:c:", ["help", "action="])
    except getopt.GetoptError, err:
        # print help information and exit:
        logging.error( str(err) )# will print something like "option -a not recognized"
        usage()
        sys.exit(2)
    action = None
    path = None
    csvfilename = None
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-a", "--action"):
            action = a
        elif o in ("-p", "--path"):
            path = a
        elif o in ("-c", "--csvfile"):
            csvfilename = a
        else:
            assert False, "unhandled option"

    logging.info( "Action : %s" % action )
    logging.info( "Path : %s" % path )

    if action == "link_fsc_partitions":
        logging.info( "Link FileSetCollection to Partitions in PartitionPool" )
        tool = fsc_partition_linker(path)
        tool.link_fsc_to_partitions()
    elif action == "make_filesets":
        logging.info( "Make Filesets" )
        tool = filesetmaker(path)
        if csvfilename is not None:
            # create a file object & pass that to make_filesets_from_csv()
            logging.info( "Making Filesets from CSV file ")
            csvfile = None
            try:
                logging.debug("Opening csv file %s" % csvfilename)
                csvfile = open(csvfilename)
                logging.debug("Got csv file object %s" % csvfile)
            except:
                logging.error("Unable to open CSV file %s" % csvfilename)
                system.exit(1)
            if csvfile is not None:
                fs_made = tool.make_filesets_from_csv(csvfile)
                for fscr in fs_made:
                    logging.info("***FileSet %s" % fscr.fileset)                    
            else:
                logging.error("CSV file object was empty...")
    elif action == "allocate":
        logging.info( "Allocate Partitions to FileSets" )
        tool = allocator(path)
        tool.allocate_round_robin()    
    elif action == "make_fsdirs":
        logging.info( "Make & link FileSet dirs" )
        tool = fsc_fileset_dir_maker(path)
        tool.make_fileset_dirs()
    else:
        logging.error( "Action not supported: %s" % action )
        usage()

if __name__=="__main__":
    main()


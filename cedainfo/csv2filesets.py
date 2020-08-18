import getopt, sys
import os, errno
import csv

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import *

def usage():
    print("Create FileSets from CSV files")
    print("Usage: %s <options> <CSVfile>" % sys.argv[0])
    print()
    print("CSVfile:")
    print("\tThis is the filename of a CSV file containing 2 columns: logical path and allocation size.")
    print("Options:")
    print("\t-u<Unit>")
    print("\t\tSets the unit for the allocation sizes (can be B, kB, MB, GB, TB)")
    print("\t-p<prefix>")
    print("\t\tPrefixes all logical paths with string")
    print("\t-t")
    print("\t\tTest run - no FileSets made")



if __name__=="__main__":

    try:
        opts, args = getopt.getopt(sys.argv[1:], "u:p:th")
    except getopt.GetoptError:
        # print help information and exit:
        usage()
        sys.exit(2)
    
    units = {"B":1,"kB":1000,"MB":1000000,"GB":1000000000,"TB":1000000000000}
    
    factor = 1
    prefix = ''
    test = False
    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
            sys.exit()
        elif o in ("-u", "--unit"):
            if a not in list(units.keys()): raise "unknown units"
            factor = units[a] 
        elif o in ("-p", "--prefix"):
            prefix = a
        elif o in ("-t", "--test"):
            test = True
        else:
            assert False, "unhandled option"
    
    csvfile = open(args[0])
    csvReader = csv.reader(csvfile, delimiter=',')
    
    for row in csvReader:
        path, size = row
        size = int(size)
        existing_filesets = FileSet.objects.filter(logical_path=path)
        if len(existing_filesets) != 0:
            print("Skip: File set with same logical path already exists")
            continue

        if not test: 
            fs = FileSet(logical_path=prefix+path, overall_final_size=size*factor)
            fs.save()
        print("makeing Fileset: %s (%s)" % (prefix+path,size*factor))
 


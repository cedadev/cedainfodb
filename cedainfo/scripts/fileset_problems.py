
from cedainfoapp.models import *

def run():
    fs_msgs = FileSet.problems()
    audit_msgs = Audit.problems()
    part_msgs = Partition.problems()
    print "http://cedadb.ceda.ac.uk/problems"
    print
    print "%s Fileset problems" % len(fs_msgs)
    print "%s Partition problems" % len(part_msgs)
    print "%s Audit problems" % len(audit_msgs)


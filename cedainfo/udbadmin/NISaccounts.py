import tempfile   
import subprocess
import passwd


def getExtGroupFile():
#
#      Return group file for external NIS
#
    a = tempfile.NamedTemporaryFile()
    p1 = subprocess.Popen(["ssh", "ypinfo@storm.badc.rl.ac.uk",  "ypcat", "group"], stdout=a)
    p1.wait()
    group = passwd.loadgrp(a.name)
    a.close()

    return group


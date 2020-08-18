import getopt, sys
import os, errno
import datetime
from datetime import *
import smtplib

from django.core.management import setup_environ
import settings
setup_environ(settings)

from .cedainfoapp.models import FileSet, Partition, FileSetSizeMeasurement




def anal(fs):
    # returns a state string and a 3 year prediction
    fssms = FileSetSizeMeasurement.objects.filter(fileset=fs).order_by('-date')

    if len(fssms) <2: return ("Not enough measurements.", fs.overall_final_size)

    nowsize = fssms[0].size
    nowtime = fssms[0].date
 
    # recommeded size is the larger of the current allocation or the current size
    recommend=max(int(nowsize*1.001), fs.overall_final_size)

    # stable filesets - if not changed in last year then recommend current size
    for i in range(len(fssms)):
        fssm = fssms[i]
        percentchange = 100.0 * (nowsize - fssm.size)/ nowsize 
        if abs(percentchange) > 1.0: break
    stable_time = nowtime - fssms[i-1].date
    stable_time = stable_time.total_seconds() /(24*3600*365.0)
    if stable_time > 2.0: return ("Stable for over 2 years", int(1.001*nowsize))
    if stable_time > 1.0: return ("Stable for over 1 year", int(1.005*nowsize))
    if stable_time > 0.5: return ("Stable for 6 months", recommend)

    # linear growth 
    for i in range(len(fssms)):
        fssm = fssms[i]
        period = nowtime - fssm.date
        period = period.total_seconds() /(24*3600*365)
        if period >0.75: 
            percentchange = 100.0 * (nowsize - fssm.size)/ nowsize 
            rate = percentchange/period
            n6months = i
            break
    else:
        return ("not long enough to look for stable growth", recommend)
    # use rate to look for regular growth pattern
    for i in range(n6months):
        fssm = fssms[i]
        period = nowtime - fssm.date
        period = period.total_seconds() /(24*3600*365)
        # predicted size 
        predicted = nowsize - nowsize * rate *0.01 * period
        if abs(predicted - fssm.size)/nowsize > 0.03: return ("Not stable", recommend)
    return ("Stable growth over 9 months", int(nowsize+nowsize*3*rate*0.01))
    


if __name__=="__main__":

    print("""script to update volume estimates for filesets that look wrong.
The script looks for filesets that are stable for more than a year and asks if they need allocations revised downwards.
If any fileset is exceeding it's allocation, or on track to exceed it, then the script will ask it it should be increased.

Answering yes to all recommendations is a bad idea as you will overwrite manually entered numbers that may be more accurate.

""")



    filesets = FileSet.objects.all()

    fs_state ={}
    fs_lists = {}
    for fs in filesets:
        state, predicted = anal(fs)
        if predicted > fs.overall_final_size: 
            print(' +++ Fileset needs more space  +++ ',fs, state, int((predicted - fs.overall_final_size)/1e9), 'GB')
            os.system("firefox http://cedadb.badc.rl.ac.uk/admin/cedainfoapp/fileset/%s" % fs.pk)
            ans = input("   Increase allocation from %s to %s? (y/n)> " % (fs.overall_final_size, predicted))
            if ans == 'y':
                fs.overall_final_size = predicted
                #fs.save()
                print("                                     ... increasing allocation.") 
        if fs.overall_final_size - predicted > 100000000000: 
            print(' --- Fileset may release alloc --- ',fs, state, int((fs.overall_final_size - predicted)/1e9), 'GB')
            os.system("firefox http://cedadb.badc.rl.ac.uk/admin/cedainfoapp/fileset/%s" % fs.pk)
            ans = input("   Decrease allocation from %s to %s? (y/n)> " % (fs.overall_final_size, predicted))
            if ans == 'y': 
                fs.overall_final_size = predicted
                #fs.save()
                print("                                     ... decreasing allocation ") 


        if state in fs_state: 
            fs_state[state] +=1
            fs_lists[state].append(fs)
        else: 
            fs_state[state] = 1
            fs_lists[state] =[fs]

#    print fs_state
#
#    print 
#    for s in fs_lists.keys():
#        print ' =============== ',s
#        
#        for fs in fs_lists[s][0:20]:
#           print "%s      http://cedadb.badc.rl.ac.uk/admin/cedainfoapp/fileset/%s" % (fs.logical_path,fs.pk)

 



    

from cedainfoapp.models import *

import datetime

def vol(from_date, search_period, path_filter):

    fms = FileSetSizeMeasurement.objects.filter(fileset__logical_path__startswith=path_filter,
                                                date__lt=from_date,
                                                date__gt=from_date - search_period).order_by('-date')
    done = []
    last = []
    for fm in fms:
        if fm.fileset in done: continue
        done.append(fm.fileset)
        last.append(fm)

    total = 0
    totalf = 0
    for fm in last:
        total+=fm.size
        if fm.no_files is not None:
            totalf += fm.no_files
    return total, totalf


def run(*args):

    search_period = datetime.timedelta(days=100)
    if len(args) == 1:
        path_filter = args[0]
    else:
        path_filter = ''

    for year in (2010, 2011, 2012, 2013, 2014, 2015, 2016):
        for month in range(1,13):

            d = datetime.datetime(year, month, 1)
            total, totalf = vol(d, search_period, path_filter)
            print '%s, %s, %s' % (d, total, totalf)



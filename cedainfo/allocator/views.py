# Create your views here.

from django.db.models import Q
from cedainfo.allocator.models import *
from django.shortcuts import redirect, render_to_response, get_object_or_404
from django.views.generic import list_detail
from django.core.urlresolvers import reverse

import datetime

# do df for a partition and redirect back to partitions list
def df(request, id):
    part = Partition.objects.get(pk=id)
    part.df()
    return redirect('/admin/allocator/partition/%s' % id)

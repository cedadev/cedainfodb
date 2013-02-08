from cedainfo.dmp.models import *
from django.shortcuts import render_to_response, get_object_or_404

def dmp_draft(request, dmp_id):
    # a summary of a single project
    dmp = get_object_or_404(DMP, pk=dmp_id)
    return render_to_response('dmp_draft.html', {'dmp': dmp,})

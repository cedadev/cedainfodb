from django.shortcuts import render_to_response, get_object_or_404
from cedainfo.rar.forms import *
from django.db.models import Count
import datetime
# Create your views here.

 

# Edit a avalibiliy
def avail(request, id):
    # make months
    startyear = 2010
    years = range(startyear, startyear+5)
    cmonths = range(1,13)
    months =[]
    for y in years:
        for m in cmonths:
	    months.append(datetime.date(y,m,1))
    
    # get person from url id
    person = Person.objects.get(pk=id)
    # for each month look for an avalibility
    avails = []
    forms =[]
    for m in months:
        try:
	    a = Availability.objects.get(person=person, month=m)
	except: 
	    a = Availability(person=person,month=m, value=0.0)
	avails.append(a)

    if request.method == 'POST':
        for a in avails :
            form = AvailForm(request.POST, instance=a, prefix=a.month)
	    forms.append(form)
            if form.is_valid():
	        form.save()
    else:
        for a in avails :
            form = AvailForm(instance=a, prefix=a.month)
	    forms.append(form)
    return render_to_response('avail.html', {'person': person, 
                                     'forms': forms, 'years':years} )


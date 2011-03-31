from django.shortcuts import render_to_response, get_object_or_404
from cedainfo.rar.forms import *
from django.db.models import Count
# Create your views here.

# Edit a avalibiliy

def avail(request, id):
       person = Person.objects.get(pk=id)
       avails = Availability.objects.filter(person=person, month__gte="2010-01-01", month__lte="2010-12-01" )
       forms = []
       if request.method == 'POST':
           for avail in avails :
               form = AvailForm(request.POST, instance=avail)
	       forms.append(form)
               if form.is_valid():
	           form.save()
       else:
           for avail in avails :
               form = AvailForm(instance=avail)
	       forms.append(form)
       return render_to_response('avail.html', {'person': person, 'forms': forms} )


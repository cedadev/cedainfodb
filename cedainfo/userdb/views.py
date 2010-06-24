from django.shortcuts import render_to_response, get_object_or_404
from cedainfo.userdb.forms import *
from django.db.models import Count
import time
# Create your views here.



def user_stats(request):
       times = [time.time()]
       if request.method == 'POST':
          form = UserStatsForm(request.POST)
          if form.is_valid():
	      role = form.cleaned_data['Role']
              # find regusers for role	  
              regusers = User.objects.filter(licence__removed=False, licence__role=role)
          else:
              form = UserStatsForm()
              # find all regusers	  
              regusers = User.objects.filter(licence__removed=False)
       else:
          form = UserStatsForm()
          # find all regusers	  
          regusers = User.objects.filter(licence__removed=False)
	
       times.append(time.time() - times[0])  

       # make list of ids 
       regusers = regusers.distinct().values_list('id', flat=True).order_by('id')
       # regusers a query. Note if you try to do this in one step you get a total number of licences not users 
       regusers = User.objects.filter(id__in=regusers)
       total = len(regusers)

       times.append(time.time() - times[0])  

       
       # users by field
       byfield = regusers.values('field').annotate(count=Count('field'))
       byfield_values = []
       byfield_labels = []
       for r in byfield:
           byfield_values.append(r['count'])
           byfield_labels.append(r['field'])

       times.append(time.time() - times[0])  

	   
       # users by area
       byarea = regusers.values('institute__country__area').annotate(count=Count('institute__country__area')).order_by('count')
       byarea_values = []
       byarea_labels = []
       for r in byarea:
           byarea_values.append(r['count'])
           byarea_labels.append(r['institute__country__area'])

       times.append(time.time() - times[0])  

       # users by instatute type
       byitype = regusers.values('institute__itype').annotate(count=Count('institute__itype')).order_by('count')
       byitype_values = []
       byitype_labels = []
       for r in byitype:
           byitype_values.append(r['count'])
           byitype_labels.append(r['institute__itype'])
	   
       times.append(time.time() - times[0])  

 	  
       return render_to_response('user_stats.html', {'form': form,
                                                     'times': times,
                                                     'total': total, 
                                                     'byfield':byfield,
						     'byfield_values':byfield_values,
						     'byfield_labels':byfield_labels,
                                                     'byarea':byarea,
						     'byarea_values':byarea_values,
						     'byarea_labels':byarea_labels,
						     'byitype':byitype,
     						     'byitype_values':byitype_values,
						     'byitype_labels':byitype_labels} )



def role_emails(request, id):
       role = Role.objects.get(pk=id)
       users = User.objects.filter(licence__removed=False, licence__role=role)
       emails = users.distinct().values_list('emailaddress', flat=True).order_by('emailaddress')

       return render_to_response('role_emails.html', {'role': role, 'emails': emails} )

# View a role (public view of a role)
def role_view(request, id):
       role = Role.objects.get(pk=id)
       return render_to_response('role_view.html', {'role': role, } )

# Edit a user
def user_form(request, id):
       user = User.objects.get(pk=id)
       if request.method == 'POST':
          form = UserForm(request.POST, instance=user)
          if form.is_valid():
	     form.save()
       else:
          form = UserForm(instance=user)
       return render_to_response('user_form.html', {'user': user, 'form': form} )

# View a user (a la MyBADC)
# TODO Should be protected so only user can see
def user_view(request, id):
       user = User.objects.get(pk=id)
       licences = Licence.objects.filter(user=user, removed=False)
       return render_to_response('user_view.html', {'user': user, 'licences':licences} )

# View a user's licences (like http://badc.nerc.ac.uk/cgi-bin/mybadc/list_datasets.cgi.pl?source=mybadc)
# TODO Should be protected so only user can see
def user_licences(request, id):
       user = User.objects.get(pk=id)
       licences_active = Licence.objects.filter(user=user, removed=False)
       licences_pending = Licence.objects.filter(user=user, removed=False) #TODO sort out filter criteria
       licences_removed = Licence.objects.filter(user=user, removed=True)
       return render_to_response('user_licences.html', {    'user': user, 
                                                            'licences_active': licences_active,
                                                            'licences_pending': licences_pending,
                                                            'licences_removed': licences_removed,} )


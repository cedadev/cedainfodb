from django.shortcuts import render_to_response, get_object_or_404
from cedainfo.userdb.forms import *
from django.db.models import Count
import time, datetime
# Create your views here.



def user_stats(request):
       times = [time.time()]
       now = datetime.datetime.now()
       if request.method == 'POST':
          form = UserStatsForm(request.POST)
          if form.is_valid():
	      role = form.cleaned_data['role']
	      group = form.cleaned_data['group']
              # find regusers for role	  
              regusers = User.objects.filter(licence__end_date__gte=now, licence__start_date__lte=now)
              regusers = regusers.filter(licence__group=group, licence__role=role)
          else:
              form = UserStatsForm()
              # find all regusers	  
              regusers = User.objects.filter(licence__end_date__gte=now, licence__start_date__lte=now)
       else:
          form = UserStatsForm()
          # find all regusers	  
          regusers = User.objects.filter(licence__end_date__gte=now, licence__start_date__lte=now)
	
       times.append(time.time() - times[0])  

       # make list of ids 
       regusers = regusers.distinct().all()
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
       #byarea = regusers.values('institute__country__area').annotate(count=Count('institute__country__area')).order_by('count')
       #byarea_values = []
       #byarea_labels = []
       #for r in byarea:
       #    byarea_values.append(r['count'])
       #    byarea_labels.append(r['institute__country__area'])

       times.append(time.time() - times[0])  

       # users by instatute type
       #byitype = regusers.values('institute__itype').annotate(count=Count('institute__itype')).order_by('count')
       #byitype_values = []
       #byitype_labels = []
       #for r in byitype:
       #    byitype_values.append(r['count'])
       #    byitype_labels.append(r['institute__itype'])
	   
       times.append(time.time() - times[0])  

 	  
       return render_to_response('user_stats.html', {'form': form,
                                                     'times': times,
                                                     'total': total,
						     'users': regusers, 
                                                     'byfield':byfield,
						     'byfield_values':byfield_values,
						     'byfield_labels':byfield_labels,
                                                   #  'byarea':byarea,
						   #  'byarea_values':byarea_values,
						   #  'byarea_labels':byarea_labels,
						   #  'byitype':byitype,
     						   #  'byitype_values':byitype_values,
						   #  'byitype_labels':byitype_labels,
						     } )



def group_emails(request, id):
       now = datetime.datetime.now()
       group = Group.objects.get(pk=id)
       users = User.objects.filter(licence__end_date__gte=now, licence__start_date__lte=now, licence__group=group)
       emails = users.distinct().values_list('email', flat=True).order_by('email')

       return render_to_response('group_emails.html', {'group': group, 'emails': emails} )

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


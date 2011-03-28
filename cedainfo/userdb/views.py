from django.shortcuts import render_to_response, get_object_or_404
from cedainfo.userdb.forms import *
from django.db.models import Count
import time, datetime, re
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



def group_emails(request, group):
       now = datetime.datetime.now()
       group = Group.objects.get(name=group)
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
	     return user_view(request, id)
       else:
          form = UserForm(instance=user)
       return render_to_response('user_form.html', {'user': user, 'form': form} )



# new user
def newuser(request):
       if request.method == 'POST':
	  user = User()
          form = NewUser(request.POST, instance=user)
          if form.is_valid():
	     # make new user
	     form.save()
	     user.update_passwd(form.cleaned_data['passwd'])
	     user.save()
	     return user_view(request, user.username)
       else:
          form = NewUser()
       return render_to_response('newuser.html', {'form': form} )
    

# Change a users password
def changepassword_form(request, id):
       passwordset = False     
       user = User.objects.get(username=id)
       if request.method == 'POST':
          form = ChangePassword(request.POST)
          if form.is_valid():
	     # change password
	     user.update_passwd(form.cleaned_data['passwd'])
	     user.save()
	     passwordset = True
	  #   return user_view(request, id)
       else:
          form = ChangePassword()
       return render_to_response('change_password.html', {'user': user, 
                                                          'form': form, 
							  'passwordset': passwordset } )


# View a user (a la MyBADC)
# TODO Should be protected so only user can see
def user_view(request, id):
    if re.match('^\d*$', id):
        user = User.objects.get(pk=id)
    else:
        user = User.objects.get(username=id)
       
    if request.method == 'POST':
        form = UserForm(request.POST, instance=user)
        if form.is_valid():
	    form.save()
    else:
        form = UserForm(instance=user)
           
    now = datetime.datetime.now()
    licences = Licence.objects.filter(user=user, end_date__gte=now, start_date__lte=now)
    return render_to_response('user_view.html', {'user': user, 'licences':licences, 
                                                  'form':form} )

# view a licence
def licence_view(request, user, group, id):
       now = datetime.datetime.now()
       licence = Licence.objects.get(pk=id)
       if user != licence.user.username: return render_to_response('bad_licence.html', {} )
       if group != licence.group.name: return render_to_response('bad_licence.html', {} )

       return render_to_response('licence_view.html', {'licence':licence} )

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


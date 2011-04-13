from django.conf.urls.defaults import *
from django.views.generic import list_detail
from cedainfoapp.models import *
from cedainfoapp.views import *
from django.conf import settings
from userdb.views import *
from userdb.models import *
from rar.views import *
from rar.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()
  
urlpatterns = patterns('',
    # Example:
    # (r'^cedainfo/', include('cedainfo.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/(.*)', admin.site.root),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.MEDIA_ROOT,'show_indexes': True}),
    # views
    # home page
    (r'^$', home),
    (r'^home/$', home),
    #  - hosts
    #   - list view of all hosts
    (r'^hosts/$', host_list),
    #   - list view of hosts subsetted (e.g. in_pool, not_retired)
    (r'^hosts/(?P<subset>\w+)$', host_list),
    #   - detail view of 1 host, by id
    (r'^host/(?P<host_id>\d+)/$', host_detail),
    # Recreate the SDDCS "nodelist" file as a view
    (r'^nodelist$', nodelist),

    # detail view of data entity
    (r'^dataentity/(?P<id>\d+)/$', dataentity_detail_form),
    (r'^dataentity/search/$', dataentity_search),
    (r'^dataentity/find/(?P<dataentity_id>.*)$', dataentity_find),
    (r'^dataentity/add/(?P<dataentity_id>.*)$', dataentity_add),
    # generic index view of all hosts
    #(r'^dataentity/index/$', list_detail.object_list, dataentity_info),
    (r'^dataentity/index/$', dataentity_list),
    (r'^dataentity/review/$', dataentities_for_review),
    (r'^fileset/index/$', fileset_list),
    (r'^fileset/(?P<id>\d+)/allocate$', allocate),
    (r'^fileset/(?P<id>\d+)/makespot$', makespot),
    (r'^fileset/(?P<id>\d+)/du$', du),
    (r'^partition/(?P<id>\d+)/df$', df),
    (r'^partition/(?P<id>\d+)/vis$', partition_vis),

    (r'^rack/services/(?P<rack_id>\d+)$', services_by_rack),

    # userdb
    (r'^userdb/userstats/$', user_stats),
    (r'^userdb/newuser/$', newuser), # TODO
    (r'^userdb/user/(?P<id>.*)/password/$', changepassword_form),
   # (r'^userdb/user/(?P<id>\d)/activate$', user_view), # for email activation #TODO
   # (r'^userdb/user/(?P<id>.*)/requestdir$', makerequestdir), #TODO
    (r'^userdb/user/(?P<id>.*)/$', user_view),
   # (r'^userdb/user/(?P<id>.*)/forgroup/(?P<group>.*)$', user_view_forauth), #TODO
   # (r'^userdb/users/passwdfile/$', passwdfile), # TODO update password file for proftpd
   # (r'^userdb/users/makefootprintsfile/$', footprintsfile), # TODO update footprints file
   # (r'^userdb/licences/groupfile/$', groupfile), # TODO update group file for proftpd
   # (r'^userdb/licences/policyfile/$', policyfile), # TODO update policy file for ESG security
   # (r'^userdb/licences/forgroup/(?P<group>.*)$', listlicences_forauth), # TODO list licences for authoriser
    (r'^userdb/licences/forgroup/(?P<group>.*)/emails/$', group_emails),
   # (r'^userdb/licences/forgroup/(?P<group>)/memview$', listlicences_formemview), # TODO list licences for membership viewer
   # (r'^userdb/appproc/(?P<id>)$', invoke_appproc), # TODO invoke appication process
    (r'^userdb/user/licences/(?P<id>\d+)/$', user_licences), # show pending user licences
    (r'^userdb/role/view/(?P<id>\d+)/$', role_view),
    (r'^userdb/licence/(?P<user>.*)/(?P<group>.*)/(?P<id>\d+)/$', licence_view),
    
    #RAR
    (r'^rar/avail/(?P<id>\d+)/$', avail),
    
    #allocator   
)

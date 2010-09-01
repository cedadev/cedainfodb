from django.conf.urls.defaults import *
from django.views.generic import list_detail
from cedainfoapp.models import *
from cedainfoapp.views import *
from django.conf import settings
from userdb.views import *
from userdb.models import *

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

    # detail view of data entity
    (r'^dataentity/(?P<id>\d+)/$', dataentity_detail_form),
    (r'^dataentity/search/$', dataentity_search),
    (r'^dataentity/find/(?P<dataentity_id>.*)$', dataentity_find),
    (r'^dataentity/add/(?P<dataentity_id>.*)$', dataentity_add),
    # generic index view of all hosts
    #(r'^dataentity/index/$', list_detail.object_list, dataentity_info),
    (r'^dataentity/index/$', dataentity_list),
    (r'^dataentity/review/$', dataentities_for_review),
    (r'^dataentity/filesets/$', dataentity_fileset_view), # TODO there's probably a better url for this...
    (r'^fileset/index/$', fileset_list),
    (r'^filesetcollection/index/$', filesetcollection_list),
    (r'^filesetcollection/index/extended/$', filesetcollection_list_extended),
    (r'^filesetcollection/(?P<id>\d+)/$', filesetcollection_view),

    (r'^rack/services/(?P<rack_id>\d+)$', services_by_rack),

    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.STATIC_DOC_ROOT,'show_indexes': True}),

    # userdb
    (r'^userdb/userstats/$', user_stats),
    (r'^userdb/user/edit/(?P<id>\d+)/$', user_form),
    (r'^userdb/user/view/(?P<id>\d+)/$', user_view),
    (r'^userdb/user/licences/(?P<id>\d+)/$', user_licences),
    (r'^userdb/role/emails/(?P<id>\d+)/$', role_emails),
    (r'^userdb/role/view/(?P<id>\d+)/$', role_view),
    
)

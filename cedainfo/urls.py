from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings
from proginfo.views import *
from proginfo.models import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from cedainfoapp.urls import urlpatterns as cedainfoapp_urlpatterns
  
urlpatterns = patterns('',
    # Example:
    # (r'^cedainfo/', include('cedainfo.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    url(r'^admin/', include(admin.site.urls)),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root':settings.MEDIA_ROOT,'show_indexes': True}),
    # views
    # home page
    
    # login/logout      
    (r'^accounts/login/$', 'django.contrib.auth.views.login'), 
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'), 

    
    # scisup proginfo tool
    (r'^programme/$', index),
    (r'^programme/(?P<prog_id>\d+)/add_proj$', add_proj),
    (r'^programme/(?P<prog_id>\d+)/DMP$', prog_DMP),
    (r'^programme/(?P<prog_id>\d+)/cost$', prog_cost),
    (r'^programme/(?P<prog_id>\d+)/add_prog_note$', add_prog_note),
    (r'^programme/(?P<prog_id>\d+)/help$', prog_help),
    (r'^project/(?P<proj_id>\d+)/add_proj_note$', add_proj_note),
    (r'^project/(?P<proj_id>\d+)/add_data$', add_data),
    (r'^project/(?P<proj_id>\d+)/DMP$', proj_DMP),
    (r'^project/(?P<proj_id>\d+)/cost$', proj_cost),
    (r'^project/(?P<proj_id>\d+)/summary$', proj_summary),
    (r'^project/(?P<proj_id>\d+)/help$', proj_help),
    (r'^dataproduct/(?P<data_id>\d+)/add_data_note$', add_data_note),
    (r'^dataproduct/(?P<data_id>\d+)/help$', data_help),

    (r'^newprojects$', newprojects),
    (r'^newproj$', add_proj_gotw),

    #(r'^udbadmin/', include('cedainfo.udbadmin.urls')),   

    (r'^dmp/', include('cedainfo.dmp.urls')),   
)

urlpatterns +=  cedainfoapp_urlpatterns



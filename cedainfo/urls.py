from django.conf.urls.defaults import *
from django.views.generic import list_detail
from django.conf import settings

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

   # (r'^udbadmin/', include('cedainfo.udbadmin.urls')),   

    (r'^dmp/', include('cedainfo.dmp.urls')),   
)

urlpatterns +=  cedainfoapp_urlpatterns



from django.conf.urls.defaults import patterns, include, url

from udbadmin.views import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'userdbadmin.views.home', name='home'),
    # url(r'^userdbadmin/', include('userdbadmin.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
     url(r'^admin/', include(admin.site.urls)),
     
     url(r'^user/datasets/current/(?P<userkey>\d{1,6})/$', list_current_user_datasets),   
     url(r'^user/datasets/removed/(?P<userkey>\d{1,6})/$', list_removed_user_datasets),        
     url(r'^dataset/details/(?P<datasetid>.+)/$', dataset_details),  
)

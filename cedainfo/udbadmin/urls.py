from django.conf.urls.defaults import patterns, include, url

from views import *
from authorise import *

from django.views.generic import list_detail


# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


urlpatterns = patterns('',
    # Examples:

    # url(r'^userdbadmin/', include('userdbadmin.foo.urls')),
    # Uncomment the admin/doc line below to enable admin documentation:
#    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    # Uncomment the next line to enable the admin:
#     url(r'^admin/', include(admin.site.urls)),

     url(r'^$', home),     
     url(r'^user/datasets/current/(?P<userkey>\d{1,6})/$', list_current_user_datasets),   
     url(r'^user/datasets/removed/(?P<userkey>\d{1,6})/$', list_removed_user_datasets),        
     url(r'^dataset/details/(?P<datasetid>.+)/$', dataset_details),     
     url(r'^authorise/(?P<userkey>\d{1,6})/$', authorise_datasets),
#     url(r'^pending/$', list_pending_datasets),
)

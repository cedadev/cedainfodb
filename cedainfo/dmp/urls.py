from django.conf.urls.defaults import patterns, include, url

from views import *

urlpatterns = patterns('',

     url(r'^project/(?P<project_id>\d+)$', dmp_draft),
     url(r'^project/(?P<project_id>\d+)/adddataproduct$', add_dataproduct),
     url(r'^myprojects$', my_projects),
)

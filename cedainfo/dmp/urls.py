from django.conf.urls.defaults import patterns, include, url

from views import *

urlpatterns = patterns('',

     url(r'^project/(?P<project_id>\d+)$', dmp_draft),
     url(r'^project/(?P<project_id>\d+)/adddataproduct$', add_dataproduct),
     url(r'^myprojects$', my_projects),
     url(r'^projectsbyperson$', projects_by_person),
     url(r'^grant/(?P<id>\d+)/scrape$', gotw_scrape),
     url(r'^grant/(?P<id>\d+)/project_from_rss_export$', make_project_from_rss_export),
     url(r'^vmreg$', vmreg),
)

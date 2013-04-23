from django.conf.urls.defaults import patterns, include, url

from views import *

urlpatterns = patterns('',

     url(r'^dmp/(?P<dmp_id>\d+)$', dmp_draft),
)

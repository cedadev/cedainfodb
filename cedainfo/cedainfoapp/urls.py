from django.conf.urls.defaults import *
from django.views.generic import list_detail
from cedainfoapp.models import *
from cedainfoapp.views import *
from django.conf import settings

  
urlpatterns = patterns('',
    (r'^$', home),
    (r'^home/$', home),
    #  - hosts
    #   - list view of all hosts
    (r'^hosts/$', host_list),
    #   - list view of hosts subsetted (e.g. in_pool, not_retired)
    (r'^hosts/(?P<subset>\w+)$', host_list),
    #   - detail view of 1 host, by id
    (r'^host/(?P<host_id>\d+)/$', host_detail),
    (r'^host/(?P<host>.*)/ftpmountscript/()$', ftpmount_script),
    (r'^host/(?P<host>.*)/automountscript/()$', automount_script),
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
    (r'^fileset/second_copy_rsyncs/$', make_secondary_copies),
    (r'^fileset/complete/$', complete_filesets),
    (r'^fileset/underallocated/$', underallocated_fs),
    (r'^fileset/(?P<id>\d+)/markcomplete', markcomplete),
    (r'^fileset/(?P<id>\d+)/allocate$', allocate),
    (r'^fileset/(?P<id>\d+)/makespot$', makespot),
    (r'^fileset/(?P<id>\d+)/du$', du),
    (r'^partition/$', partition_list),
    (r'^partition/(?P<id>\d+)/df$', df),
    (r'^partition/(?P<id>\d+)/vis$', partition_vis),
    (r'^latest/volumes/$', VolFeed()),

    (r'^rack/services/(?P<rack_id>\d+)$', services_by_rack),
    (r'^storagesummary$', storagesummary),
    (r'^storage-d/spotlist$', storaged_spotlist),
    (r'^external/storage-d/spotlist$', storaged_spotlist_public),
    (r'^detailed_spotlist$', detailed_spotlist),
    
    (r'^gwsrequest/(?P<id>\d+)/approve', approve_gwsrequest),
    (r'^gwsrequest/(?P<id>\d+)/reject', reject_gwsrequest),
    (r'^gwsrequest/(?P<id>\d+)/convert', convert_gwsrequest),
    (r'^gwsrequest/index/$', gwsrequest_list), # list for external viewers
    (r'^gwsrequest/(?P<id>\d+)/$', gwsrequest_detail), #detail view for external viewers    

	(r'^gws/(?P<id>\d+)/update', create_gws_update_request),
    (r'^gws/index/$', gws_list), # list for external viewers
    
    (r'^vmrequest/(?P<id>\d+)/approve', approve_vmrequest),
    (r'^vmrequest/(?P<id>\d+)/reject', reject_vmrequest),
    (r'^vmrequest/(?P<id>\d+)/convert', convert_vmrequest),
    (r'^vmrequest/index/$', vmrequest_list), # list for external viewers
    (r'^vmrequest/(?P<id>\d+)/$', vmrequest_detail), #detail view for external viewers 
    
    (r'^vm/(?P<id>\d+)/update', create_vm_update_request),
    (r'^vm/(?P<id>\d+)/changestatus', change_status),


    #    audit views
    (r'^audit_totals$', audit_totals),


)

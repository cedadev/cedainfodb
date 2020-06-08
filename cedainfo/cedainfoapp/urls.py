from django.conf.urls import *
from cedainfoapp.models import *
from cedainfoapp.views import *
from django.conf import settings

  
urlpatterns = [
    url(r'^$', home),
    url(r'^home/$', home),
    url(r'^problems/$', problems),
    #  - hosts
    #   - list view of all hosts

    url(r'^hosts/$', HostList.as_view()),

#    url(r'^hosts/$', host_list),
    #   - list view of hosts subsetted url(e.g. in_pool, not_retired)
#    url(r'^hosts/(?P<subset>\w+)$', host_list),
 
    url(r'^services/listbyvm/$', service_list_by_vm),
    url(r'^services/list4team/$', service_list_for_team_members),
    url(r'^services/owner_managers/$', service_owner_manager_list),

    url(r'^services/internetfacing/$', service_internet_facing),    
    url(r'^services/unusedvms/$', service_unusedvms),
    url(r'^services/review/$', service_review_selection),
    url(r'^services/doc-check/$', service_doc_check),
    url(r'^services/decomissioned-doc-check/$', decomissioned_service_doc_check),

    url(r'^vm-ping-check/$', vm_ping_check),
        
    url(r'^txt/hosts/$', txt_host_list),
    url(r'^txt/vms/(?P<vmname>.*)$', txt_vms_list),
    url(r'^txt/vmrequests/$', txt_vm_request_list), 
    url(r'^txt/services/(?P<vmname>.*)$', txt_service_list),
    url(r'^txt/services2/(?P<vmname>.*)$', txt_service_list2),          
    #   - detail view of 1 host, by id
    url(r'^host/(?P<host_id>\d+)/$', host_detail),
    # Recreate the SDDCS "nodelist" file as a view
    #url(r'^nodelist$', nodelist),

    url(r'^fileset/index/$', fileset_list),
    url(r'^fileset/second_copy_rsyncs/$', make_secondary_copies),
    url(r'^fileset/primary_on_tape/$', primary_on_tape),
    url(r'^fileset/download_conf/$', download_conf),
    url(r'^fileset/complete/$', complete_filesets),
    url(r'^fileset/spotlist/$', spotlist),
    url(r'^fileset/underallocated/$', underallocated_fs),
    url(r'^fileset/(?P<id>\d+)/markcomplete', markcomplete),
    url(r'^fileset/(?P<id>\d+)/du$', du),
    url(r'^partition/$', partition_list),
    url(r'^partition/(?P<id>\d+)/df$', df),
    url(r'^partition/(?P<id>\d+)/vis$', partition_vis),
    url(r'^partition/(?P<id>\d+)/peplerdiagram$', partition_peplerdiagram),
    url(r'^latest/volumes/$', VolFeed()),

    url(r'^storagesummary$', storagesummary),
    url(r'^storage-d/spotlist$', storaged_spotlist),
    url(r'^external/storage-d/spotlist$', storaged_spotlist_public),
    url(r'^detailed_spotlist$', detailed_spotlist),
    
    url(r'^gwsrequest/(?P<id>\d+)/approve', approve_gwsrequest),
    url(r'^gwsrequest/(?P<id>\d+)/reject', reject_gwsrequest),
    url(r'^gwsrequest/(?P<id>\d+)/convert', convert_gwsrequest),
    url(r'^gwsrequest/index/$', gwsrequest_list), # list for external viewers
    url(r'^gwsrequest/(?P<id>\d+)/$', gwsrequest_detail), #detail view for external viewers    

    url(r'^gws/(?P<id>\d+)/update', create_gws_update_request),
    url(r'^gws/index/$', gws_list), # list for external viewers
    url(r'^gws/dashboard/$', gws_dashboard), # dashboard with more detail
    url(r'^gws/(?P<id>\d+)/du$', gwsdu), # du to create size measurement for GWS
    url(r'^gws/(?P<id>\d+)/df$', gwsdf), # du to create size measurement for GWS
    url(r'^gws/etexport/$', gws_list_etexport), # list for export to Elastic Tape system
    
    url(r'^vmrequest/(?P<id>\d+)/approve', approve_vmrequest),
    url(r'^vmrequest/(?P<id>\d+)/reject', reject_vmrequest),
    url(r'^vmrequest/(?P<id>\d+)/convert', convert_vmrequest),
    url(r'^vmrequest/index/$', vmrequest_list), # list for external viewers
    url(r'^vmrequest/(?P<id>\d+)/$', vmrequest_detail), #detail view for external viewers 
    
    url(r'^vm/(?P<id>\d+)/update', create_vm_update_request),
    url(r'^vm/(?P<id>\d+)/changestatus', change_status),

]

from django.conf.urls import *
from cedainfoapp.models import *
from cedainfoapp.views import *
from django.conf import settings
from django.urls import path, re_path

urlpatterns = [
    path("", home),
    path("home/", home),
    path("problems/", problems),
    #  - hosts
    #   - list view of all hosts
    path("hosts/", HostList.as_view()),
    #    url(r'^hosts/$', host_list),
    #   - list view of hosts subsetted url(e.g. in_pool, not_retired)
    #    url(r'^hosts/(?P<subset>\w+)$', host_list),
    path("services/uptimerobot/", uptimerobot_monitors),
    path("services/uptimerobot-check/", service_uptime_robot_check),
    path("services/listbyvm/", service_list_by_vm),
    path("services/list4team/", service_list_for_team_members),
    path("services/certcheck/", service_cert_check),
    path("services/owner_managers/", service_owner_manager_list),
    path("services/internetfacing/", service_internet_facing),
    path("services/unusedvms/", service_unusedvms),
    path("services/review/", service_review_selection),
    path("services/doc-check/", service_doc_check),
    path("services/decomissioned-doc-check/", decomissioned_service_doc_check),
    path("services/stats/", service_stats),
    path("vm-ping-check/", vm_ping_check),
    path("txt/hosts/", txt_host_list),
    re_path(r"^txt/vms/(?P<vmname>.*)$", txt_vms_list),
    path("txt/vmrequests/", txt_vm_request_list),
    re_path(r"^txt/services/(?P<vmname>.*)$", txt_service_list),
    re_path(r"^txt/services2/(?P<vmname>.*)$", txt_service_list2),
    #   - detail view of 1 host, by id
    path("host/<int:host_id>/", host_detail),
    # Recreate the SDDCS "nodelist" file as a view
    # url(r'^nodelist$', nodelist),
    path("fileset/index/", fileset_list),
    path("fileset/second_copy_rsyncs/", make_secondary_copies),
    path("fileset/primary_on_tape/", primary_on_tape),
    path("fileset/download_conf/", download_conf),
    path("fileset/complete/", complete_filesets),
    path("fileset/spotlist/", spotlist),
    path("fileset/underallocated/", underallocated_fs),
    re_path(r"^fileset/(?P<id>\d+)/markcomplete", markcomplete),
    path("fileset/<int:id>/du", du),
    path("partition/", partition_list),
    path("partition/<int:id>/df", df),
    path("partition/<int:id>/vis", partition_vis),
    path("partition/<int:id>/peplerdiagram", partition_peplerdiagram),
    path("latest/volumes/", VolFeed()),
    path("storagesummary", storagesummary),
    path("storage-d/spotlist", storaged_spotlist),
    path("external/storage-d/spotlist", storaged_spotlist_public),
    path("detailed_spotlist", detailed_spotlist),
    re_path(r"^gwsrequest/(?P<id>\d+)/approve", approve_gwsrequest),
    re_path(r"^gwsrequest/(?P<id>\d+)/reject", reject_gwsrequest),
    re_path(r"^gwsrequest/(?P<id>\d+)/convert", convert_gwsrequest),
    path("gwsrequest/index/", gwsrequest_list),  # list for external viewers
    path(
        "gwsrequest/<int:id>/", gwsrequest_detail
    ),  # detail view for external viewers
    re_path(r"^gws/(?P<id>\d+)/update", create_gws_update_request),
    path("gws/index/", gws_list),  # list for external viewers
    path("gws/dashboard/", gws_dashboard),  # dashboard with more detail
    path("gws/<int:id>/du", gwsdu),  # du to create size measurement for GWS
    path("gws/<int:id>/df", gwsdf),  # du to create size measurement for GWS
    path(
        "gws/etexport/", gws_list_etexport
    ),  # list for export to Elastic Tape system
    re_path(r"^vmrequest/(?P<id>\d+)/approve", approve_vmrequest),
    re_path(r"^vmrequest/(?P<id>\d+)/reject", reject_vmrequest),
    re_path(r"^vmrequest/(?P<id>\d+)/convert", convert_vmrequest),
    path("vmrequest/index/", vmrequest_list),  # list for external viewers
    path(
        "vmrequest/<int:id>/", vmrequest_detail
    ),  # detail view for external viewers
    re_path(r"^vm/(?P<id>\d+)/update", create_vm_update_request),
    re_path(r"^vm/(?P<id>\d+)/changestatus", change_status),
]

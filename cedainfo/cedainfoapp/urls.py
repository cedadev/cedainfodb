from django.conf.urls import *
from cedainfoapp.models import *
from cedainfoapp.views import *
from django.conf import settings
from django.urls import path, re_path

urlpatterns = [
    path("", home),
    path("home/", home),
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

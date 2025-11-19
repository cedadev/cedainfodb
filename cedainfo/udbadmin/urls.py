from django.urls import path, re_path

from .views import *
from .authorise import *
from .jasmin import *
from .udb_ldap_views import *
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    path('', home), 
    path('user/accountid/<path:accountid>/', user_edit_by_accountid),    
    re_path(r'^user/datasets/current/(?P<userkey>-?\d{1,6})/$', list_current_user_datasets),   
    re_path(r'^user/datasets/removed/(?P<userkey>-?\d{1,6})/$', list_removed_user_datasets),        

    path('user/keys/', list_keys),        
    re_path(r'^external/user/account-details/(?P<userkey>\d{1,6})/$', user_account_details),
    re_path(r'^user/getemail/(?P<accountid>[\d\w]+)$', user_getemail),

    re_path(r'^user/datasets/add/(?P<userkey>\d{1,6})/$', add_user_datasets), 

    re_path(r'^user/change-password/(?P<userkey>\d{1,6})/$', change_user_password),        

    path('dataset/details/<path:datasetid>/', dataset_details),    
    path('dataset/users/<path:datasetid>/', list_users_for_dataset),
    path('dataset/accounts/<path:datasetid>/', list_accounts_for_dataset),
        
    path('dataset/email/<path:datasetid>/', list_users_email_for_dataset),     

    path('jasmin/list_users/<path:tag>/', list_jasmin_users), 
    path('jasmin/list_users/', list_jasmin_users), 

    path('jasmin/group/<path:group>', ldap_group_details), 
    path('jasmin/group/', ldap_list_groups), 

    re_path(r'^ldap/user/diff/(?P<userkey>-?\d{1,6})', ldap_udb_user_diff), 
    re_path(r'^ldap/user/ldif/(?P<userkey>-?\d{1,6})', ldap_udb_user_ldif),
    path('ldap/newusers/', udp_ldap_new_members),

    path('ldap/user/<path:accountid>', ldap_user_details), 
    re_path(r'^ldap/udbuser/(?P<userkey>-?\d{1,6})', ldap_udb_user), 

    path('ldap/user/', ldap_udb_users), 

    path('ldap/nis/external/passwd', display_nis_external_passwd), 
    path('ldap/nis/internal/passwd', display_nis_internal_passwd), 

    path('ldapext/group/', ldap_udb_groups),   

    path('ldap/write/', write_to_ldap_server),
        
    path('ldap/list_root_users', ldap_list_root_users),
    
    path('ldap/list_root_users_byuser', ldap_list_root_users2),
        
    path('ldap/ldapusers/', ldap_users),    
    re_path(r'^ldap/ldapuser/(?P<uid>-?\d{1,7})', ldap_user),    

    path('ldap/group/', ldap_udb_groups),   
        
    path('ldap/ldapgroups/', ldap_groups),
    path('ldap/ldapgroupsfiltered/', ldap_groups_filtered),

    re_path(r'^ldap/ldapusergroups/(?P<userkey>-?\d{1,6})$', ldap_user_groups),

    path('ldap/groupdiff/', ldap_group_diff),
    path('ldap/groupldif/', ldap_group_ldiff),

    path('ldap/userdiff/', ldap_user_diff),
    path('ldap/userldif/', ldap_user_ldiff),
        
    path('ldapext/nis/group/<path:datasetid>', write_nis_group), 
    path('ldapext/nis/group/', write_all_nis_groups),            

    path('ldapext/group/<path:datasetid>', write_ldap_group), 
    path('ldapext/group/', ldap_udb_groups),   
    path('ldapext/ldapgroups/', ldap_groups),

    path('ldapext/updatecheck/', check_udb_for_updates),
            
        
    re_path(r'^authorise/(?P<userkey>-?\d{1,6})/$', authorise_datasets),
    re_path(r'^udj/(?P<id>\d{1,6})/$', edit_user_dataset_join),
    re_path(r'^request/(?P<id>\d{1,6})/$', edit_dataset_request),
    path('ldap/accessdenied/',  TemplateView.as_view(template_name='accessdenied.html')),

]

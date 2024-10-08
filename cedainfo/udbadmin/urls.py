from django.conf.urls import include, url

from .views import *
from .authorise import *
from .jasmin import *
from .udb_ldap_views import *
from django.views.generic import TemplateView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^$', home), 
    url(r'^user/accountid/(?P<accountid>.+)/$', user_edit_by_accountid),    
    url(r'^user/datasets/current/(?P<userkey>-?\d{1,6})/$', list_current_user_datasets),   
    url(r'^user/datasets/removed/(?P<userkey>-?\d{1,6})/$', list_removed_user_datasets),        

    url(r'^user/keys/$', list_keys),        
    url(r'^external/user/account-details/(?P<userkey>\d{1,6})/$', user_account_details),
    url(r'^user/getemail/(?P<accountid>[\d\w]+)$', user_getemail),

    url(r'^user/datasets/add/(?P<userkey>\d{1,6})/$', add_user_datasets), 

    url(r'^user/change-password/(?P<userkey>\d{1,6})/$', change_user_password),        

    url(r'^dataset/details/(?P<datasetid>.+)/$', dataset_details),    
    url(r'^dataset/users/(?P<datasetid>.+)/$', list_users_for_dataset),
    url(r'^dataset/accounts/(?P<datasetid>.+)/$', list_accounts_for_dataset),
        
    url(r'^dataset/email/(?P<datasetid>.+)/$', list_users_email_for_dataset),     

    url(r'^jasmin/list_users/(?P<tag>.+)/$', list_jasmin_users), 
    url(r'^jasmin/list_users/$', list_jasmin_users), 

    url(r'^jasmin/group/(?P<group>.+)$', ldap_group_details), 
    url(r'^jasmin/group/$', ldap_list_groups), 

    url(r'^ldap/user/diff/(?P<userkey>-?\d{1,6})', ldap_udb_user_diff), 
    url(r'^ldap/user/ldif/(?P<userkey>-?\d{1,6})', ldap_udb_user_ldif),
    url(r'^ldap/newusers/$', udp_ldap_new_members),

    url(r'^ldap/user/(?P<accountid>.+)$', ldap_user_details), 
    url(r'^ldap/udbuser/(?P<userkey>-?\d{1,6})', ldap_udb_user), 

    url(r'^ldap/user/$', ldap_udb_users), 

    url(r'^ldap/nis/external/passwd$', display_nis_external_passwd), 
    url(r'^ldap/nis/internal/passwd$', display_nis_internal_passwd), 

    url(r'^ldapext/group/$', ldap_udb_groups),   

    url(r'^ldap/write/$', write_to_ldap_server),
        
    url(r'^ldap/list_root_users$', ldap_list_root_users),
    
    url(r'^ldap/list_root_users_byuser$', ldap_list_root_users2),
        
    url(r'^ldap/ldapusers/$', ldap_users),    
    url(r'^ldap/ldapuser/(?P<uid>-?\d{1,7})', ldap_user),    

    url(r'^ldap/group/$', ldap_udb_groups),   
        
    url(r'^ldap/ldapgroups/$', ldap_groups),
    url(r'^ldap/ldapgroupsfiltered/$', ldap_groups_filtered),

    url(r'^ldap/ldapusergroups/(?P<userkey>-?\d{1,6})$', ldap_user_groups),

    url(r'^ldap/groupdiff/$', ldap_group_diff),
    url(r'^ldap/groupldif/$', ldap_group_ldiff),

    url(r'^ldap/userdiff/$', ldap_user_diff),
    url(r'^ldap/userldif/$', ldap_user_ldiff),
        
    url(r'^ldapext/nis/group/(?P<datasetid>.+)$', write_nis_group), 
    url(r'^ldapext/nis/group/$', write_all_nis_groups),            

    url(r'^ldapext/group/(?P<datasetid>.+)$', write_ldap_group), 
    url(r'^ldapext/group/$', ldap_udb_groups),   
    url(r'^ldapext/ldapgroups/$', ldap_groups),

    url(r'^ldapext/updatecheck/$', check_udb_for_updates),
            
        
    url(r'^authorise/(?P<userkey>-?\d{1,6})/$', authorise_datasets),
    url(r'^udj/(?P<id>\d{1,6})/$', edit_user_dataset_join),
    url(r'^request/(?P<id>\d{1,6})/$', edit_dataset_request),
    url(r'^ldap/accessdenied/$',  TemplateView.as_view(template_name='accessdenied.html')),

]

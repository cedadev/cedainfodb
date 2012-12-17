from django.conf.urls.defaults import patterns, include, url

from views import *
from authorise import *
from jasmin import *
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
     url(r'^user/accountid/(?P<accountid>.+)/$', user_edit_by_accountid),    
     url(r'^user/datasets/current/(?P<userkey>\d{1,6})/$', list_current_user_datasets),   
     url(r'^user/datasets/removed/(?P<userkey>\d{1,6})/$', list_removed_user_datasets),        

     url(r'^user/keys/$', list_keys),        
     url(r'^external/user/account-details/(?P<userkey>\d{1,6})/$', user_account_details),
      
     url(r'^user/datasets/add/(?P<userkey>\d{1,6})/$', add_user_datasets),        

     url(r'^dataset/details/(?P<datasetid>.+)/$', dataset_details),    
     url(r'^dataset/users/(?P<datasetid>.+)/$', list_users_for_dataset),
     url(r'^dataset/accounts/(?P<datasetid>.+)/$', list_accounts_for_dataset),
          
     url(r'^dataset/email/(?P<datasetid>.+)/$', list_users_email_for_dataset),     

     url(r'^jasmin/check_linux_groups/$', check_linux_groups),     
     url(r'^jasmin/nis_group_entries/$', nis_group_entries),     

     url(r'^jasmin/list_users/(?P<tag>.+)/$', list_jasmin_users), 
     url(r'^jasmin/list_users/$', list_jasmin_users), 

     url(r'^jasmin/group/(?P<group>.+)$', ldap_group_details), 
     url(r'^jasmin/group/$', ldap_list_groups), 
     
     url(r'^ldap/user/(?P<accountid>.+)$', ldap_user_details),      
     url(r'^ldap/list_root_users$', ldap_list_root_users),
           
     url(r'^authorise/(?P<userkey>\d{1,6})/$', authorise_datasets),
     url(r'^udj/(?P<id>\d{1,6})/$', edit_user_dataset_join),
     url(r'^request/(?P<id>\d{1,6})/$', edit_dataset_request),

#     url(r'^pending/$', list_pending_datasets),
)

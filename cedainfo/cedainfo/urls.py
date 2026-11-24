
from django.urls import include, path, re_path
from django.urls import path
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth import views as auth_views

from cedainfoapp.urls import urlpatterns as cedainfoapp_urlpatterns
from cedainfoapp.views import AdminLoginView

urlpatterns = [
    path("admin/login/", AdminLoginView.as_view()),
    path("admin/", admin.site.urls),
    path("oidc/", include("mozilla_django_oidc.urls")),

#    url(r'^accounts/login/$', login, name='login'),
#    url(r'^accounts/logout/$', logout_then_login),
#    path('udbadmin/', include('udbadmin.urls')),
#    url(r'^cedainfoapp/', include('cedainfoapp.urls')),    
]

urlpatterns +=  cedainfoapp_urlpatterns

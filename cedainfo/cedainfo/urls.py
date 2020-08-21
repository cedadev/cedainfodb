"""cedainfo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from django.urls import path
from django.contrib import admin
from django.contrib.auth import login
from django.contrib.auth import views as auth_views

from cedainfoapp.urls import urlpatterns as cedainfoapp_urlpatterns
urlpatterns = [
    url(r'^admin/', admin.site.urls),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
#    url(r'^accounts/login/$', login, name='login'),
#    url(r'^accounts/logout/$', logout_then_login),
    url(r'^udbadmin/', include('udbadmin.urls')),
#    url(r'^cedainfoapp/', include('cedainfoapp.urls')),    
]

urlpatterns +=  cedainfoapp_urlpatterns

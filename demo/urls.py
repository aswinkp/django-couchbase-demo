"""demo URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
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
from django.contrib import admin
from couch.views import *

address_urls = [
    url(r'^$', address, name="address_list" ),
    url(r'^create/$', address_create, name="address_create" ),
    url(r'^update/(?P<id>[\W\w]+)/$', address_update, name="address_update" ),
    url(r'^show/(?P<id>[\W\w]+)/$', address_show, name="address_show" ),
    url(r'^delete/(?P<id>[\W\w]+)/$', address_delete, name="address_delete"),
]
article_urls = [
    url(r'^$', article, name="article_list" ),
    url(r'^create/$', article_create, name="article_create" ),
    url(r'^update/(?P<id>[\W\w]+)/$', article_update, name="article_update" ),
    url(r'^show/(?P<id>[\W\w]+)/$', article_show, name="article_show" ),
    url(r'^delete/(?P<id>[\W\w]+)/$', article_delete, name="article_delete"),
]

urlpatterns = [
    url(r'^$', form, name="home" ),
    url(r'^admin/', admin.site.urls),
    url(r'^address/', include(address_urls)),
    url(r'^article/', include(article_urls)),
]


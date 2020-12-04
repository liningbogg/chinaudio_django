"""pitch URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from django.conf.urls import url
from django.conf.urls import include
from django.contrib import admin
from web.views import WebView
from django.views.generic.base import RedirectView

web_view = WebView()
#favicon_view = RedirectView.as_view(url='/static/favicon.ico', permanent=True)

urlpatterns = [
    path('', web_view.index),
    path('admin/', admin.site.urls),
    path('web/', include('web.urls')),
    path('target/', include('target.urls')),
    path('ocr/', include('ocr.urls')),
    #url(r'^favicon\.ico$', favicon_view),
]

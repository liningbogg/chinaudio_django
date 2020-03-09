from web.views import WebView
from django.urls import path
from django.conf.urls import include
from django.conf.urls import url

web_view = WebView()

# admin.autodiscover()
urlpatterns = [
    path('index/', web_view.index),
    path('accounts/login/', web_view.login),
    path('accounts/logout/', web_view.logout),
    path('accounts/register/', web_view.register),
    url(r'^captcha', include('captcha.urls')),
    url('^$', web_view.index),
]

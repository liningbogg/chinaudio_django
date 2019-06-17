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
Including another URLconf:q
uu
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import include
from django.conf.urls import url
from django.contrib import admin
from django.urls import path

from target.views import TargetView

target_view = TargetView()
admin.autodiscover()
urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', target_view.index),
    path('copywaves/', target_view.copywaves),
    path('copywaves/sub_and_execute/', target_view.sub_and_execute_copywaves),
    path('wave/', target_view.wave_view),
    path('wave/get_phrase/', target_view.get_phrase),
    path('labeling/get_phrase/', target_view.get_phrase),
    path('wave/post_phrase/', target_view.post_phrase),
    path('wave/access/', target_view.db_access),
    path('labeling/', target_view.labeling),
    path('login/', target_view.login),
    path('accounts/login/', target_view.login),
    path('logout/', target_view.logout),
    path('register/', target_view.register),
    path('wave/get_clipFFT/', target_view.get_clipfft),
    path('labeling/cal_pitch_pos/', target_view.cal_pitch_pos),
    path('labeling/filter_fft/', target_view.filter_fft),
    url(r'^captcha', include('captcha.urls')),
    url('^$', target_view.index),
]

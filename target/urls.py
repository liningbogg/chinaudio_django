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
from django.contrib.staticfiles.views import serve


target_view = TargetView()
admin.autodiscover()
urlpatterns = [
    path('admin/', admin.site.urls),
    path('index/', target_view.index),
    path('addwaves/', target_view.addwaves),
    path('copywaves/', target_view.copywaves),
    path('copywaves/sub_and_execute/', target_view.sub_and_execute_copywaves),
    path('wave/', target_view.wave_view),
    path('wave/get_phrase/', target_view.get_phrase),
    path('labeling/get_phrase/', target_view.get_phrase),
    path('wave/post_phrase/', target_view.post_phrase),
    path('wave/access/', target_view.db_access),
    path('digital/',target_view.digital),
    path('digital/ocrPDF_assist_request/',target_view.ocrPDF_assist_request),
    path('digital/ocrPDF_assist_request/sub_and_execute/',target_view.sub_and_execute_assist_ocr),
    path('digital/ocrPDF_assist_in_accept/',target_view.ocrPDF_assist_request_accept),
    path('digital/ocrPDF_assist_in_deny/',target_view.ocrPDF_assist_request_deny),
    path('digital/ocrPDF_assist_out_delete/',target_view.ocrPDF_assist_request_delete),
    path('labeling/', target_view.labeling),
    path('login/', target_view.login),
    path('accounts/login/', target_view.login),
    path('logout/', target_view.logout),
    path('register/', target_view.register),
    path('wave/get_clipFFT/', target_view.get_clip_fft),
    path('labeling/cal_pitch_pos/', target_view.cal_pitch_pos),
    path('labeling/filter_fft/', target_view.filter_fft),
    path('labeling/algorithm_select/', target_view.algorithm_select),
    path('labeling/algorithm_clear/', target_view.algorithm_clear),
    path('labeling/algorithm_cal/', target_view.algorithm_cal),
    path('labeling/reference_select/', target_view.reference_select),
    path('labeling/addReference/', target_view.add_reference),
    path('labeling/delReference/', target_view.del_reference),
    path('labeling/calStft/', target_view.cal_stft),
    path('labeling/setPrimary/', target_view.set_primary),
    path('labeling/setRefFilter/', target_view.set_ref_filter),
    path('labeling/calRmse/', target_view.cal_rmse),
    path('labeling/calEE/', target_view.cal_ee),
    path('labeling/setManualPos/', target_view.set_manual_pos),
    path('labeling/calCustomPitch/', target_view.cal_custom_pitch),
    path('index/addTune/', target_view.add_tune),
    path('labeling/tune_reset/', target_view.tune_reset),  # 此处是指根据曲调重新设置弦高的危险算操作
    path('labeling/strings_reset/', target_view.strings_reset),
    path('labeling/labeling_reset/', target_view.labeling_reset),
    path('labeling/get_spectrogram/', target_view.get_spectrogram),
    path('addpdfs/', target_view.addpdfs),
    path('ocr_labeling/', target_view.ocr_labeling),
    path('ocr_labeling/get_image/', target_view.ocr_get_image),
    path('ocr_labeling/move_page/', target_view.ocr_move_page),
    path('ocr_labeling/add_labeling_polygon/', target_view.add_labeling_polygon),
    path('ocr_labeling/delete_all_polygon/', target_view.delete_all_polygon),
    path('ocr_labeling/delete_region/', target_view.delete_region),
    path('ocr_labeling/rotate_degree_reset/', target_view.rotate_degree_reset),
    path('ocr_labeling/rough_labeling/', target_view.rough_labeling),
    # path('favicon.ico', serve, {'path': '/image/favicon.ico'}),
    url(r'^captcha', include('captcha.urls')),
    url('^$', target_view.index),
]

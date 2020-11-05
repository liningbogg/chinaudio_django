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
from django.urls import path
from target.views import TargetView
from django.contrib.staticfiles.views import serve


target_view = TargetView()
urlpatterns = [
    path('index/', target_view.index),
    path('addwaves/', target_view.addwaves),
    path('copywaves/', target_view.copywaves),
    path('copywaves/sub_and_execute/', target_view.sub_and_execute_copywaves),
    path('waves/', target_view.waves),
    path('wave/get_phrase/', target_view.get_phrase),
    path('labeling/get_phrase/', target_view.get_phrase),
    path('wave/post_phrase/', target_view.post_phrase),
    path('wave/access/', target_view.db_access),
    path('labeling/', target_view.labeling),
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
    path('addTune/', target_view.add_tune),
    path('tunes/', target_view.tunes),
    path('getLabelingconfigure/', target_view.get_labelingconfigure),
    path('getReferenceinfo/', target_view.get_referenceinfo),
    path('setReferenceFilter/', target_view.set_reference_filter),
    path('enableAlgorithm/', target_view.enable_algorithm),
    path('disableAlgorithm/', target_view.disable_algorithm),
    path('refRecalculate/', target_view.ref_recalculate),
    path('getVad/', target_view.get_vad),
    path('getPrimaryrefinfo/', target_view.get_primaryrefinfo),
    path('getPrimaryReference/', target_view.get_primary_reference),
    path('getBasefrqCustom/', target_view.get_basefrq_custom),
    path('getPhrase/', target_view.get_phrase),
    path('getSpectrum/', target_view.get_spectrum),
    path('getReferencepitch/', target_view.get_referencepitch),
    path('getLabelingpitch/', target_view.get_labelingpitch),
    path('nextframe/', target_view.nextframe),
    path('labeling/tune_reset/', target_view.tune_reset),  # 此处是指根据曲调重新设置弦高的危险算操作
    path('labeling/strings_reset/', target_view.strings_reset),
    path('labeling/labeling_reset/', target_view.labeling_reset),
    path('labeling/get_spectrogram/', target_view.get_spectrogram),
    # path('favicon.ico', serve, {'path': '/image/favicon.ico'}),
]

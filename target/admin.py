from django.contrib import admin

from target.models import Clip
from target.models import Log
from target.models import MarkedPhrase
from target.models import Tone
from target.models import Wave
from target.models import Stft
from target.models import LabelingAlgorithmsConf
from target.models import Tune
from target.models import TargetUser
from target.models import OcrPDF
from target.models import PDFImage

# Register your models here.
admin.site.register(Clip)
admin.site.register(Tone)
admin.site.register(MarkedPhrase)
admin.site.register(Wave)
admin.site.register(Log)
admin.site.register(Stft)
admin.site.register(LabelingAlgorithmsConf)
admin.site.register(Tune)
admin.site.register(TargetUser)
admin.site.register(OcrPDF)
admin.site.register(PDFImage)


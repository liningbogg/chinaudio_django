from django.contrib import admin

from target.models import Clip
from target.models import Log
from target.models import MarkedPhrase
from target.models import Tone
from target.models import Wave

# Register your models here.
admin.site.register(Clip)
admin.site.register(Tone)
admin.site.register(MarkedPhrase)
admin.site.register(Wave)
admin.site.register(Log)

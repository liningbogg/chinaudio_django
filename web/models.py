from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class PitchUser(AbstractUser):
    wavefileRoot= models.CharField(max_length=255, default="/home/liningbo/waveFiles")
    test = models.CharField(max_length=255,null=True)
    session_key = models.CharField(max_length=255,null=True)

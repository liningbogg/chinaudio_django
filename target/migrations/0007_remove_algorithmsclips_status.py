# Generated by Django 2.2.2 on 2019-06-24 04:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0006_algorithmsclips_status'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='algorithmsclips',
            name='status',
        ),
    ]

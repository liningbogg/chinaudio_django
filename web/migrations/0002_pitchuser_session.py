# Generated by Django 2.2.2 on 2019-12-31 09:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('web', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='pitchuser',
            name='session',
            field=models.CharField(max_length=255, null=True),
        ),
    ]
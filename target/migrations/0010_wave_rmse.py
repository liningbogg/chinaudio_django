# Generated by Django 2.2.2 on 2020-07-03 02:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0009_remove_wave_rmse'),
    ]

    operations = [
        migrations.AddField(
            model_name='wave',
            name='rmse',
            field=models.CharField(default='', max_length=255),
        ),
    ]
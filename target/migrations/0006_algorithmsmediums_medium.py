# Generated by Django 2.2.2 on 2020-07-02 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0005_remove_algorithmsmediums_medium'),
    ]

    operations = [
        migrations.AddField(
            model_name='algorithmsmediums',
            name='medium',
            field=models.CharField(default='', max_length=255),
        ),
    ]

# Generated by Django 2.2.2 on 2020-07-02 02:43

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0002_auto_20200102_0759'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='clip',
            name='src',
        ),
    ]

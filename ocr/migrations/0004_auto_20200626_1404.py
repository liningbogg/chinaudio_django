# Generated by Django 2.2.2 on 2020-06-26 14:04

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0003_auto_20200626_1354'),
    ]

    operations = [
        migrations.AlterField(
            model_name='characterelem',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='chineseelem',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='imageuserconf',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='ocrassist',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='ocrassistrequest',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='ocrlabelingpolygon',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='ocrpdf',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='pdfimage',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
        migrations.AlterField(
            model_name='polygonelem',
            name='update_time',
            field=models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间'),
        ),
    ]
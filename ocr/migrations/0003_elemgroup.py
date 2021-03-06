# Generated by Django 3.1.2 on 2020-12-16 05:41

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0002_chineseelem_image_bytes'),
    ]

    operations = [
        migrations.CreateModel(
            name='ElemGroup',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, help_text='添加时间', verbose_name='添加时间')),
                ('update_time', models.DateTimeField(default=datetime.datetime.now, help_text='更新时间', verbose_name='更新时间')),
                ('create_user_id', models.CharField(help_text='创建人id', max_length=255, verbose_name='创建人id')),
                ('is_deleted', models.BooleanField(default=False)),
                ('name', models.CharField(max_length=255)),
                ('desc', models.CharField(max_length=255)),
            ],
            options={
                'unique_together': {('name', 'create_user_id')},
            },
        ),
    ]

# Generated by Django 3.1.2 on 2020-12-22 02:57

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0007_remove_chineseelem_elemgroup'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='ElemGroup',
            new_name='Ocrmodel',
        ),
    ]

# Generated by Django 3.1.2 on 2020-12-17 01:48

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0005_remove_chineseelem_elem_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='chineseelem',
            name='elemgroup',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='ocr.elemgroup'),
        ),
    ]

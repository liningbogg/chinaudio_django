# Generated by Django 2.2.2 on 2020-05-14 09:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='ocrlabelingpolygon',
            name='labeling_content',
            field=models.BooleanField(default=False),
        ),
    ]

# Generated by Django 2.2.2 on 2020-04-15 13:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0005_auto_20200415_0556'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ocrlabelingpolygon',
            name='labeling_content',
            field=models.BinaryField(default=False),
        ),
    ]
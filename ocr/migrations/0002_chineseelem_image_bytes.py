# Generated by Django 3.1.2 on 2020-12-05 03:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='chineseelem',
            name='image_bytes',
            field=models.CharField(max_length=256, null=True),
        ),
    ]
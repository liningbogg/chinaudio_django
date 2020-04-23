# Generated by Django 2.2.2 on 2020-04-23 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0011_auto_20200423_2105'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='characterelem',
            name='height',
        ),
        migrations.RemoveField(
            model_name='characterelem',
            name='width',
        ),
        migrations.AddField(
            model_name='chineseelem',
            name='height',
            field=models.IntegerField(default=128),
        ),
        migrations.AddField(
            model_name='chineseelem',
            name='width',
            field=models.IntegerField(default=128),
        ),
    ]
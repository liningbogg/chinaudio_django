# Generated by Django 3.1.2 on 2020-12-16 05:46

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0003_elemgroup'),
    ]

    operations = [
        migrations.AddField(
            model_name='chineseelem',
            name='elem_group',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='ocr.elemgroup'),
        ),
    ]
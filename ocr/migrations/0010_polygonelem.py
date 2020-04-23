# Generated by Django 2.2.2 on 2020-04-22 06:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('ocr', '0009_auto_20200419_0923'),
    ]

    operations = [
        migrations.CreateModel(
            name='PolygonElem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_time', models.DateTimeField(auto_now_add=True, help_text='添加时间', verbose_name='添加时间')),
                ('create_user_id', models.CharField(help_text='创建人id', max_length=255, verbose_name='创建人id')),
                ('is_deleted', models.BooleanField(default=False)),
                ('desc_info', models.TextField(default='')),
                ('elem', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ocr.ChineseElem')),
                ('polygon', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ocr.OcrLabelingPolygon')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
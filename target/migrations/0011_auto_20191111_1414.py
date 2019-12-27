# Generated by Django 2.2.2 on 2019-11-11 14:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0010_auto_20191111_1332'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='ocrassistrequest',
            name='status',
        ),
        migrations.AddField(
            model_name='ocrassist',
            name='assist_user_name',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterUniqueTogether(
            name='ocrassist',
            unique_together={('ocrPDF', 'assist_user_name')},
        ),
    ]
# Generated by Django 2.2.2 on 2020-01-02 07:59

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('target', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='imageuserconf',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='imageuserconf',
            name='image',
        ),
        migrations.AlterUniqueTogether(
            name='ocrassist',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='ocrassist',
            name='ocrPDF',
        ),
        migrations.DeleteModel(
            name='OcrAssistRequest',
        ),
        migrations.RemoveField(
            model_name='ocrlabelingpolygon',
            name='pdfImage',
        ),
        migrations.AlterUniqueTogether(
            name='ocrpdf',
            unique_together=None,
        ),
        migrations.AlterUniqueTogether(
            name='pdfimage',
            unique_together=None,
        ),
        migrations.RemoveField(
            model_name='pdfimage',
            name='ocrPDF',
        ),
        migrations.DeleteModel(
            name='ImageUserConf',
        ),
        migrations.DeleteModel(
            name='OcrAssist',
        ),
        migrations.DeleteModel(
            name='OcrLabelingPolygon',
        ),
        migrations.DeleteModel(
            name='OcrPDF',
        ),
        migrations.DeleteModel(
            name='PDFImage',
        ),
    ]

# Generated by Django 5.1.3 on 2024-12-02 01:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('spotify', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='song',
            name='album',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='genre',
            field=models.CharField(max_length=255, null=True),
        ),
        migrations.AlterField(
            model_name='song',
            name='image',
            field=models.FileField(null=True, upload_to='song_images/'),
        ),
    ]

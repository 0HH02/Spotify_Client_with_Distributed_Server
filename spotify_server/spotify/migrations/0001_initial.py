# Generated by Django 5.1.3 on 2024-12-01 23:53

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Song',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255)),
                ('artist', models.CharField(max_length=255)),
                ('album', models.CharField(max_length=255)),
                ('genre', models.CharField(max_length=255)),
                ('image', models.FileField(upload_to='song_images/')),
                ('audio', models.FileField(upload_to='songs/')),
            ],
        ),
    ]
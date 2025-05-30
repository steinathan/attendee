# Generated by Django 5.1.2 on 2025-05-18 11:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0028_botmediarequest_media_url_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='recording',
            name='transcription_failure_data',
            field=models.JSONField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='utterance',
            name='failure_data',
            field=models.JSONField(default=None, null=True),
        ),
        migrations.AddField(
            model_name='utterance',
            name='transcription_attempt_count',
            field=models.IntegerField(default=0),
        ),
    ]

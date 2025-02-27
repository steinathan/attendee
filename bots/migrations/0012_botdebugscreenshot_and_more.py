# Generated by Django 5.1.2 on 2025-02-11 15:32

import bots.models
import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bots', '0011_alter_credentials_credential_type'),
    ]

    operations = [
        migrations.CreateModel(
            name='BotDebugScreenshot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_id', models.CharField(editable=False, max_length=32, unique=True)),
                ('metadata', models.JSONField(default=dict)),
                ('file', models.FileField(storage=bots.models.BotDebugScreenshotStorage(), upload_to='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.RemoveConstraint(
            model_name='botevent',
            name='valid_event_type_event_sub_type_combinations',
        ),
        migrations.RemoveField(
            model_name='botevent',
            name='debug_message',
        ),
        migrations.AddField(
            model_name='botevent',
            name='metadata',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='botevent',
            name='event_sub_type',
            field=models.IntegerField(choices=[(1, 'Bot could not join meeting - Meeting Not Started - Waiting for Host'), (2, 'Fatal error - Process Terminated'), (3, 'Bot could not join meeting - Zoom Authorization Failed'), (4, 'Bot could not join meeting - Zoom Meeting Status Failed'), (5, 'Bot could not join meeting - Unpublished Zoom Apps cannot join external meetings. See https://developers.zoom.us/blog/prepare-meeting-sdk-app-for-review'), (6, 'Fatal error - RTMP Connection Failed'), (7, 'Bot could not join meeting - Zoom SDK Internal Error'), (8, 'Fatal error - UI Element Not Found'), (9, 'Bot could not join meeting - Request to join denied')], null=True),
        ),
        migrations.AddConstraint(
            model_name='botevent',
            constraint=models.CheckConstraint(condition=models.Q(models.Q(('event_type', 7), models.Q(('event_sub_type', 2), ('event_sub_type', 6), ('event_sub_type', 8), _connector='OR')), models.Q(('event_type', 9), models.Q(('event_sub_type', 1), ('event_sub_type', 3), ('event_sub_type', 4), ('event_sub_type', 5), ('event_sub_type', 7), ('event_sub_type', 9), _connector='OR')), models.Q(models.Q(('event_type', 7), _negated=True), models.Q(('event_type', 9), _negated=True), ('event_sub_type__isnull', True)), _connector='OR'), name='valid_event_type_event_sub_type_combinations'),
        ),
        migrations.AddField(
            model_name='botdebugscreenshot',
            name='bot_event',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='debug_screenshots', to='bots.botevent'),
        ),
    ]

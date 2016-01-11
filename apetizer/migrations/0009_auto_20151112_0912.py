# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0008_auto_20151027_1123'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datapath',
            name='related',
        ),
        migrations.AddField(
            model_name='moderation',
            name='related',
            field=models.ForeignKey(related_name='relations', blank=True, to='apetizer.Item', null=True),
        ),
    ]

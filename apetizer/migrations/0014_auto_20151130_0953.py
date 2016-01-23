# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0013_location_search_ranking'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='nickname',
        ),
        migrations.AlterField(
            model_name='datapath',
            name='data',
            field=models.TextField(default=b'{}', null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='translation',
            name='slug',
            field=models.CharField(default=b'', max_length=128),
        ),
        migrations.AlterField(
            model_name='translation',
            name='title',
            field=models.CharField(max_length=156),
        ),
    ]

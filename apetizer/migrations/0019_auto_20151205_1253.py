# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0018_auto_20151205_1658'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='datapath',
            name='geojson',
        ),
        migrations.AddField(
            model_name='item',
            name='geojson',
            field=models.TextField(null=True, verbose_name='GeoJSON data field', blank=True),
        ),
    ]

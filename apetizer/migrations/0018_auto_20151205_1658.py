# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0017_auto_20151205_0904'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='location',
            name='item',
        ),
        migrations.AddField(
            model_name='item',
            name='latitude',
            field=models.FloatField(null=True, verbose_name='latitude', blank=True),
        ),
        migrations.AddField(
            model_name='item',
            name='longitude',
            field=models.FloatField(null=True, verbose_name='longitude', blank=True),
        ),
        migrations.DeleteModel(
            name='Location',
        ),
    ]

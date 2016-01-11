# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0019_auto_20151205_1253'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='end',
            field=models.DateTimeField(null=True, verbose_name='End Date', blank=True),
        ),
        migrations.AddField(
            model_name='item',
            name='start',
            field=models.DateTimeField(null=True, verbose_name='Start Date', blank=True),
        ),
    ]

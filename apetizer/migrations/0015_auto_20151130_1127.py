# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0014_auto_20151130_0953'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='type',
            field=models.CharField(default=b'view', max_length=65),
        ),
        migrations.AlterField(
            model_name='datapath',
            name='data',
            field=models.TextField(default=b'{}', null=True, blank=True),
        ),
    ]

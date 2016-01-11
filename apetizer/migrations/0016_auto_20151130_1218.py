# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0015_auto_20151130_1127'),
    ]

    operations = [
        migrations.AlterField(
            model_name='datapath',
            name='data',
            field=models.TextField(default={}, null=True, blank=True),
        ),
    ]

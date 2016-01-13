# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0022_auto_20160106_0949'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='item',
            name='type',
        ),
        migrations.AddField(
            model_name='datapath',
            name='type',
            field=models.CharField(default=b'Thing', max_length=65),
        ),
        migrations.AlterField(
            model_name='item',
            name='behavior',
            field=models.CharField(default=b'view', max_length=65),
        ),
    ]

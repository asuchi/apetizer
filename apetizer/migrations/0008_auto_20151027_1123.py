# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0007_auto_20151026_1938'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='translation',
            name='enabled',
        ),
        migrations.AlterField(
            model_name='datapath',
            name='modified_date',
            field=models.DateTimeField(verbose_name='modified on', null=True, editable=False, blank=True),
        ),
    ]

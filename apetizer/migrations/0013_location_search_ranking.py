# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0012_auto_20151122_1400'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='search_ranking',
            field=models.IntegerField(default=0, null=True, blank=True),
        ),
    ]

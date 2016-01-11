# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0002_auto_20151016_0945'),
    ]

    operations = [
        migrations.AddField(
            model_name='visitor',
            name='validated',
            field=models.DateTimeField(null=True, verbose_name='validated on', blank=True),
        ),
    ]

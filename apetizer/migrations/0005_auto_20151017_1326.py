# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0004_remove_visitor_valid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='visitor',
            name='validated',
            field=models.DateTimeField(null=True, verbose_name='Date de validation', blank=True),
        ),
    ]

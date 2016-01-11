# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0003_visitor_validated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='visitor',
            name='valid',
        ),
    ]

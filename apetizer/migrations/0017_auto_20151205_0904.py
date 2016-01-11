# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0016_auto_20151130_1218'),
    ]

    operations = [
        migrations.RenameField(
            model_name='datapath',
            old_name='geodata',
            new_name='geojson',
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import apetizer.models


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0011_auto_20151122_1225'),
    ]

    operations = [
        migrations.AddField(
            model_name='location',
            name='visible',
            field=models.BooleanField(default=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='id',
            field=models.CharField(default=apetizer.models.get_new_uuid, max_length=128, serialize=False, editable=False, primary_key=True),
        ),
        migrations.AlterField(
            model_name='location',
            name='item',
            field=models.ForeignKey(related_name='locations', to='apetizer.Item'),
        ),
    ]

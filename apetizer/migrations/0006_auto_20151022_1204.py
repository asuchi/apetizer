# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0005_auto_20151017_1326'),
    ]

    operations = [
        migrations.AddField(
            model_name='moderation',
            name='origin',
            field=models.ForeignKey(related_name='moderations', blank=True, to='apetizer.Moderation', null=True),
        ),
        migrations.AlterField(
            model_name='translation',
            name='description',
            field=models.TextField(blank=True),
        ),
    ]

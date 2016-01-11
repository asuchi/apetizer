# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0009_auto_20151112_0912'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='behavior',
            field=models.CharField(default=b'view', max_length=65, choices=[(b'view', b'Article'), (b'image', b'Image'), (b'map', b'Carte'), (b'agenda', b'Agenda'), (b'tree', b'Arborescence'), (b'related', b'Related service')]),
        ),
        migrations.AlterField(
            model_name='moderation',
            name='related',
            field=models.ForeignKey(related_name='relations', to='apetizer.Item'),
        ),
        migrations.AlterField(
            model_name='visitor',
            name='username',
            field=models.CharField(max_length=65, null=True, blank=True),
        ),
    ]

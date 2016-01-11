# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0006_auto_20151022_1204'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='related_cron',
            field=models.CharField(default=b'live', max_length=65, choices=[(b'live', b'Au chargement'), (b'once', b'Une fois'), (b'every-hour', b'Toutes les heures'), (b'every-day', b'Tous les jours'), (b'every-week', b'Une fois par semaine'), (b'every-month', b'Bon ben tous les mois ...')]),
        ),
        migrations.AlterField(
            model_name='translation',
            name='title',
            field=models.CharField(max_length=128),
        ),
    ]

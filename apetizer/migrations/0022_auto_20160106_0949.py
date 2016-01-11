# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0021_frontend'),
    ]

    operations = [
        migrations.AddField(
            model_name='frontend',
            name='login',
            field=models.CharField(default=b'bee', max_length=12),
        ),
        migrations.AddField(
            model_name='frontend',
            name='password',
            field=models.CharField(default=b'honeypot', max_length=12),
        ),
        migrations.AddField(
            model_name='frontend',
            name='published',
            field=models.BooleanField(default=False),
        ),
    ]

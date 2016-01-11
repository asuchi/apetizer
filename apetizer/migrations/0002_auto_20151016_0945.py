# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='visitor',
            old_name='name',
            new_name='username',
        ),
        migrations.RenameField(
            model_name='visitor',
            old_name='validated',
            new_name='valid',
        ),
    ]

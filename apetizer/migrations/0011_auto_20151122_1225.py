# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('apetizer', '0010_auto_20151115_0954'),
    ]

    operations = [
        migrations.CreateModel(
            name='Location',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('latitude', models.FloatField(null=True, verbose_name='latitude', blank=True)),
                ('longitude', models.FloatField(null=True, verbose_name='longitude', blank=True)),
                ('fuzzy_latitude', models.FloatField(verbose_name='fuzzy latitude', null=True, editable=False, blank=True)),
                ('fuzzy_longitude', models.FloatField(verbose_name='fuzzy longitude', null=True, editable=False, blank=True)),
                ('timezone', models.CharField(help_text='Designates which time zone this location is in.', max_length=255, null=True, verbose_name='time zone', blank=True)),
                ('nickname', models.CharField(max_length=100, null=True, verbose_name='nickname', blank=True)),
                ('full_address', models.CharField(max_length=200, null=True, verbose_name='address', blank=True)),
                ('town', models.CharField(db_index=True, max_length=100, null=True, verbose_name='town', blank=True)),
                ('postal_code', models.CharField(db_index=True, max_length=20, null=True, verbose_name='postal code', blank=True)),
                ('country', models.CharField(default='FR', max_length=2, db_index=True, blank=True)),
                ('administrative_area_one', models.CharField(max_length=100, blank=True, help_text='US states, FR regions', null=True, verbose_name='area level 1', db_index=True)),
                ('administrative_area_two', models.CharField(max_length=100, blank=True, help_text='US counties, FR departments', null=True, verbose_name='area level 2', db_index=True)),
                ('ref_time', models.BigIntegerField(editable=False)),
                ('created_date', models.DateTimeField(verbose_name='created on', editable=False)),
                ('modified_date', models.DateTimeField(verbose_name='modified on', null=True, editable=False, blank=True)),
                ('completed_date', models.DateTimeField(verbose_name='completed on', null=True, editable=False, blank=True)),
            ],
            options={
                'abstract': False,
                'verbose_name': 'address',
                'verbose_name_plural': 'addresses',
            },
        ),
        migrations.RemoveField(
            model_name='item',
            name='end',
        ),
        migrations.RemoveField(
            model_name='item',
            name='start',
        ),
        migrations.AlterField(
            model_name='moderation',
            name='origin',
            field=models.ForeignKey(related_name='replys', blank=True, to='apetizer.Moderation', null=True),
        ),
        migrations.AlterField(
            model_name='moderation',
            name='related',
            field=models.ForeignKey(related_name='events', to='apetizer.Item'),
        ),
        migrations.AddField(
            model_name='location',
            name='item',
            field=models.ForeignKey(to='apetizer.Item'),
        ),
    ]

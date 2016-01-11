# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import apetizer.models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DataPath',
            fields=[
                ('ref_time', models.BigIntegerField(editable=False)),
                ('id', models.CharField(default=apetizer.models.get_new_uuid, max_length=128, serialize=False, editable=False, primary_key=True)),
                ('akey', models.CharField(max_length=128)),
                ('action', models.CharField(max_length=65)),
                ('path', models.CharField(max_length=512)),
                ('data', models.TextField(default=b'{}', null=True, blank=True)),
                ('geohash', models.CharField(default=b'', max_length=12, null=True, blank=True)),
                ('geodata', models.TextField(null=True, verbose_name='GeoJSON data field', blank=True)),
                ('locale', models.CharField(max_length=6)),
                ('visible', models.BooleanField(default=True)),
                ('created_date', models.DateTimeField(verbose_name='created on', editable=False)),
                ('modified_date', models.DateTimeField(verbose_name='modified on', editable=False)),
                ('completed_date', models.DateTimeField(verbose_name='completed on', null=True, editable=False, blank=True)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Visitor',
            fields=[
                ('datapath_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='apetizer.DataPath')),
                ('email', models.EmailField(max_length=156, null=True, blank=True)),
                ('name', models.CharField(max_length=65, blank=True)),
                ('validated', models.NullBooleanField(default=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('apetizer.datapath',),
        ),
        migrations.CreateModel(
            name='Moderation',
            fields=[
                ('visitor_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='apetizer.Visitor')),
                ('status', models.CharField(default=b'', max_length=20)),
                ('evaluation', models.IntegerField(default=0, blank=True)),
                ('subscribed', models.NullBooleanField(default=True)),
                ('subject', models.CharField(max_length=156, null=True, blank=True)),
                ('message', models.CharField(max_length=4048, null=True, blank=True)),
                ('is_busy', models.NullBooleanField(default=False, editable=False)),
                ('is_sent', models.NullBooleanField(default=False, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=('apetizer.visitor',),
        ),
        migrations.CreateModel(
            name='Translation',
            fields=[
                ('moderation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='apetizer.Moderation')),
                ('slug', models.CharField(default=b'', max_length=256)),
                ('enabled', models.BooleanField(default=False)),
                ('label', models.CharField(max_length=65)),
                ('title', models.CharField(max_length=125)),
                ('description', models.TextField(max_length=156, blank=True)),
                ('content', models.TextField(blank=True)),
                ('redirect_url', models.TextField(verbose_name=b'Redirection url', blank=True)),
            ],
            options={
                'abstract': False,
            },
            bases=('apetizer.moderation',),
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('translation_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='apetizer.Translation')),
                ('order', models.IntegerField(default=0)),
                ('image', models.ImageField(null=True, upload_to=apetizer.models.upload_to, blank=True)),
                ('file', models.FileField(max_length=255, null=True, upload_to=apetizer.models.upload_to, blank=True)),
                ('related_url', models.URLField(null=True, verbose_name='Related URL', blank=True)),
                ('behavior', models.CharField(default=b'view', max_length=65, choices=[(b'view', b'Article'), (b'Item', b'Article'), (b'image', b'Image'), (b'upload', b'Fichier'), (b'map', b'Carte'), (b'agenda', b'Agenda'), (b'tree', b'Arborescence')])),
                ('start', models.DateTimeField(null=True, verbose_name='Start Date', blank=True)),
                ('end', models.DateTimeField(null=True, verbose_name='End Date', blank=True)),
                ('published', models.NullBooleanField()),
                ('parent', models.ForeignKey(related_name='children', blank=True, to='apetizer.Item', null=True)),
            ],
            options={
                'ordering': ('order',),
            },
            bases=('apetizer.translation',),
        ),
        migrations.AddField(
            model_name='datapath',
            name='related',
            field=models.ForeignKey(related_name='relations', blank=True, to='apetizer.Item', null=True),
        ),
    ]

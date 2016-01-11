# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import apetizer.forms.frontend


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        ('apetizer', '0020_auto_20151207_1039'),
    ]

    operations = [
        migrations.CreateModel(
            name='Frontend',
            fields=[
                ('site_ptr', models.OneToOneField(parent_link=True, auto_created=True, primary_key=True, serialize=False, to='sites.Site')),
                ('folder_name', apetizer.forms.frontend.FolderNameField(help_text=b"Folder name for this site's files.  The name may only consist of lowercase characters, numbers (0-9), and/or underscores", max_length=64, blank=True)),
                ('subdomains', apetizer.forms.frontend.SubdomainListField(help_text=b'Comma separated list of subdomains this site supports.  Leave blank to support all subdomains', blank=True)),
            ],
            bases=('sites.site',),
        ),
    ]

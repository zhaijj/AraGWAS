# -*- coding: utf-8 -*-
# Generated by Django 1.11b1 on 2017-03-03 14:47
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('gwasdb', '0003_auto_20170302_1614'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='snp',
            name='name',
        ),
    ]

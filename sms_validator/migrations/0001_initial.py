# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='SMSToken',
            fields=[
                ('key', models.CharField(max_length=40, serialize=False, verbose_name='token', primary_key=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('is_active', models.BooleanField(default=True, verbose_name='is active')),
                ('phone_number', models.CharField(max_length=20, verbose_name='phone')),
                ('slug', models.SlugField(null=True, verbose_name='slug', blank=True)),
                ('validating_id', models.PositiveIntegerField(verbose_name='object ID')),
                ('validating_type', models.ForeignKey(verbose_name='content type', to='contenttypes.ContentType', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ('-created_at',),
                'verbose_name': 'SMS token',
                'verbose_name_plural': 'SMS tokens',
            },
        ),
    ]

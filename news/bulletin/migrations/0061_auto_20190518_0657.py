# Generated by Django 2.1.4 on 2019-05-18 06:57

import bulletin.models
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0060_topic_numitems'),
    ]

    operations = [
        migrations.AlterField(
            model_name='profile',
            name='catorder',
            field=models.CharField(blank=True, default="['Politics', 'Business', 'International', 'Custom topics']", max_length=1000),
        ),
        migrations.AlterField(
            model_name='profile',
            name='sources',
            field=models.ManyToManyField(blank=True, default=bulletin.models.Profile.defaultsources, to='bulletin.Source'),
        ),
    ]

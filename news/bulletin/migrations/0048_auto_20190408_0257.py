# Generated by Django 2.1.4 on 2019-04-08 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0047_auto_20190405_0336'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='story_itemscore_factor',
            field=models.SmallIntegerField(default=8),
        ),
        migrations.AddField(
            model_name='category',
            name='story_keywords_factor',
            field=models.SmallIntegerField(default=2),
        ),
        migrations.AddField(
            model_name='category',
            name='story_numitems_factor',
            field=models.SmallIntegerField(default=10),
        ),
        migrations.AddField(
            model_name='category',
            name='story_sources_factor',
            field=models.SmallIntegerField(default=2),
        ),
        migrations.AddField(
            model_name='category',
            name='story_tracker_factor',
            field=models.SmallIntegerField(default=5),
        ),
    ]
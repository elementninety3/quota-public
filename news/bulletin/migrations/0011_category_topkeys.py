# Generated by Django 2.1.4 on 2018-12-26 21:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0010_story_category'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='topkeys',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
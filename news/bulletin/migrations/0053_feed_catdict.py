# Generated by Django 2.1.4 on 2019-04-18 02:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0052_userstory_score'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='catdict',
            field=models.CharField(default='{}', max_length=5000),
        ),
    ]

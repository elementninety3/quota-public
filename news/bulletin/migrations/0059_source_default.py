# Generated by Django 2.1.4 on 2019-05-01 04:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0058_auto_20190429_0307'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='default',
            field=models.BooleanField(default=True),
        ),
    ]

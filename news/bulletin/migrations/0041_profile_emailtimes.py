# Generated by Django 2.1.4 on 2019-03-18 15:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0040_auto_20190316_0406'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='emailtimes',
            field=models.CharField(default='[]', max_length=150),
        ),
    ]

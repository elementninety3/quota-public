# Generated by Django 2.1.4 on 2019-03-03 01:59

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0025_item_elapsed_hours'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='score',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=4),
        ),
        migrations.AddField(
            model_name='story',
            name='tracker',
            field=models.SmallIntegerField(default=0),
        ),
    ]

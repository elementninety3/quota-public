# Generated by Django 2.1.4 on 2019-04-08 03:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0048_auto_20190408_0257'),
    ]

    operations = [
        migrations.AddField(
            model_name='story',
            name='score',
            field=models.DecimalField(decimal_places=10, max_digits=30, null=True),
        ),
    ]
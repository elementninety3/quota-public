# Generated by Django 2.1.4 on 2019-03-03 18:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0027_auto_20190303_0224'),
    ]

    operations = [
        migrations.AddField(
            model_name='item',
            name='top_image',
            field=models.CharField(blank=True, max_length=2000),
        ),
        migrations.AddField(
            model_name='story',
            name='tagline',
            field=models.CharField(blank=True, max_length=500, null=True),
        ),
    ]
# Generated by Django 2.1.4 on 2019-02-27 03:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0014_auto_20190227_0256'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='items',
            field=models.ManyToManyField(blank=True, to='bulletin.Item'),
        ),
    ]

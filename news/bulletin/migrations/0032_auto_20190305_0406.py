# Generated by Django 2.1.4 on 2019-03-05 04:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0031_topic_user'),
    ]

    operations = [
        migrations.AlterField(
            model_name='item',
            name='date',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]

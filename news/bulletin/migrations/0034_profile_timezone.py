# Generated by Django 2.1.4 on 2019-03-06 16:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0033_profile_catorder'),
    ]

    operations = [
        migrations.AddField(
            model_name='profile',
            name='timezone',
            field=models.CharField(choices=[('US Eastern Time', 'US/Eastern'), ('US Central Time', 'US/Central'), ('US Mountain Time', 'US/Mountain'), ('US Pacific Time', 'US/Pacific')], max_length=40, null=True),
        ),
    ]

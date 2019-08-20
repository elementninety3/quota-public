# Generated by Django 2.1.4 on 2019-03-07 02:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0034_profile_timezone'),
    ]

    operations = [
        migrations.AddField(
            model_name='topic',
            name='categories',
            field=models.ManyToManyField(blank=True, to='bulletin.Category'),
        ),
        migrations.AlterField(
            model_name='profile',
            name='timezone',
            field=models.CharField(choices=[('US/Eastern', 'US Eastern Time'), ('US/Central', 'US Central Time'), ('US/Mountain', 'US Mountain Time'), ('US/Pacific', 'US Pacific Time')], max_length=40, null=True),
        ),
    ]
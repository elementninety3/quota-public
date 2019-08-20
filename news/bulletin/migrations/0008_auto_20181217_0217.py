# Generated by Django 2.1.4 on 2018-12-17 02:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0007_auto_20181217_0215'),
    ]

    operations = [
        migrations.AddField(
            model_name='feed',
            name='newsource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bulletin.Source'),
        ),
        migrations.AddField(
            model_name='item',
            name='newsource',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bulletin.Source'),
        ),
    ]
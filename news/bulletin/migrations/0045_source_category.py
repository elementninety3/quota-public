# Generated by Django 2.1.4 on 2019-03-30 16:34

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0044_auto_20190327_1315'),
    ]

    operations = [
        migrations.AddField(
            model_name='source',
            name='category',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bulletin.Category'),
        ),
    ]

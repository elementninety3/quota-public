# Generated by Django 2.1.4 on 2019-04-05 03:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0046_category_url_filter'),
    ]

    operations = [
        migrations.AlterField(
            model_name='category',
            name='url_filter',
            field=models.CharField(default='[]', max_length=2000),
        ),
    ]

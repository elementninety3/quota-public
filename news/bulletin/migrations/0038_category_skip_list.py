# Generated by Django 2.1.4 on 2019-03-12 04:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0037_category_filter_words'),
    ]

    operations = [
        migrations.AddField(
            model_name='category',
            name='skip_list',
            field=models.CharField(blank=True, max_length=2000),
        ),
    ]
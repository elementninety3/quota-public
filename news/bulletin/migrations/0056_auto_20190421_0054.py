# Generated by Django 2.1.4 on 2019-04-21 00:54

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0055_auto_20190420_1851'),
    ]

    operations = [
        migrations.AlterField(
            model_name='topic',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='topics', to=settings.AUTH_USER_MODEL),
        ),
    ]

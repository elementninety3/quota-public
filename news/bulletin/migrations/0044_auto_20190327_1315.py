# Generated by Django 2.1.4 on 2019-03-27 13:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bulletin', '0043_auto_20190327_0308'),
    ]

    operations = [
        migrations.CreateModel(
            name='EmailSend',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('day', models.SmallIntegerField()),
                ('time', models.CharField(max_length=10)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.RemoveField(
            model_name='profile',
            name='emaildaytimes',
        ),
        migrations.AlterField(
            model_name='profile',
            name='emailformdata',
            field=models.CharField(default='[{}]', max_length=400),
        ),
    ]

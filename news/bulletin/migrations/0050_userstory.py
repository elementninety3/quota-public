# Generated by Django 2.1.4 on 2019-04-16 02:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('bulletin', '0049_story_score'),
    ]

    operations = [
        migrations.CreateModel(
            name='UserStory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lead', models.CharField(blank=True, max_length=1000, null=True)),
                ('leadlink', models.CharField(blank=True, max_length=500, null=True)),
                ('image', models.CharField(blank=True, max_length=2000, null=True)),
                ('tagline', models.CharField(blank=True, max_length=500, null=True)),
                ('leadsource', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='bulletin.Source')),
                ('story', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='bulletin.Story')),
            ],
        ),
    ]
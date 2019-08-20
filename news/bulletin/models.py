from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver

from datetime import datetime, timedelta

from django.utils import timezone

from django.urls import reverse

# Create your models here.

# Category management for feeds and news items


TIMEZONES = (
    ('US/Eastern','US/Eastern'),
    ('US/Central','US/Central'),
    ('US/Mountain','US/Mountain'),
    ('US/Pacific','US/Pacific')
)

class Category(models.Model):
    category = models.CharField(max_length=40)
    topkeys = models.CharField(max_length=300, null=True, blank=True)
    topkeyvals = models.CharField(max_length=300, null=True, blank=True)
    words_factor = models.CharField(max_length=10, default='3')
    keys_factor = models.CharField(max_length=10, default='2')
    filter_words = models.CharField(max_length=2000, blank=True)
    skip_list = models.CharField(max_length=2000, blank=True)
    url_filter = models.CharField(max_length=2000, default='[]')
    story_itemscore_factor = models.SmallIntegerField(default=8)
    story_keywords_factor = models.SmallIntegerField(default=2)
    story_numitems_factor = models.SmallIntegerField(default=10)
    story_tracker_factor = models.SmallIntegerField(default=5)
    story_sources_factor = models.SmallIntegerField(default=2)

    def __str__(self):
        return self.category

class Source(models.Model):
    source = models.CharField(max_length=30)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    default = models.BooleanField(default=True)

    def __str__(self):
        try:
            sourcecat = self.category.category
        except:
            sourcecat = "Null"
        return self.source + " - " + sourcecat

    def displayname(self):
        return self.source


# Stories, determined by keywords in news items

class Story(models.Model):
    keywords = models.CharField(max_length=200, blank=True, null=True)
    numitems = models.IntegerField(null=True, blank=True)
    leadsource = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    lead = models.CharField(max_length=1000, blank=True, null=True)
    leadlink = models.CharField(max_length=500, blank=True, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='stories')
    image = models.CharField(max_length=2000, blank=True, null=True)
    tracker = models.SmallIntegerField(default=0)
    tagline = models.CharField(max_length=500, blank=True, null=True)
    numkeys = models.SmallIntegerField(default=0)
    score = models.DecimalField(max_digits=30, decimal_places=10, null=True)
    new_story = models.BooleanField(default=True)
    to_delete = models.BooleanField(default=False)

    def __str__(self):
        return self.keywords + " - " + self.category.category

class UserStory(models.Model):
    story = models.ForeignKey(Story, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    lead = models.CharField(max_length=1000, blank=True, null=True)
    leadlink = models.CharField(max_length=500, blank=True, null=True)
    image = models.CharField(max_length=2000, blank=True, null=True)
    tagline = models.CharField(max_length=500, blank=True, null=True)
    leadsource = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    score = models.DecimalField(max_digits=30, decimal_places=10, null=True)

    def __str__(self):
        return self.user.username + ' - ' + self.story.keywords


# Individual news items

class Item(models.Model):
    title = models.CharField(max_length=500)
    link = models.CharField(max_length=2000)
    desc = models.CharField(max_length=600)
    desc_wc = models.IntegerField(default=0)
    date = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    source = models.CharField(max_length=30, null=True)
    newsource = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    keywords = models.CharField(max_length=500, null=True)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    story = models.ForeignKey(Story, on_delete=models.SET_NULL, null=True, blank=True, related_name='items')
    elapsed_hours = models.IntegerField(default=48)
    score = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    top_image = models.CharField(max_length=2000, blank=True)
    allwords = models.CharField(max_length=5500, blank=True)
    slug = models.CharField(max_length=600, blank=True)

    def __str__(self):
        return self.title or ''

    def published_24(self):
        return self.date >= (timezone.now() - timedelta(days=1))

    def get_elapsed_hours(self):
        try:
            timediff = (timezone.now() - self.date)
            return int(timediff.total_seconds() / 3600)
        except:
            return 35

# Feeds (to make adding new sources easy and possibly enable filtering by source for users)

class Feed(models.Model):
    title = models.CharField(max_length=100)
    source = models.CharField(max_length=30, null=True)
    newsource = models.ForeignKey(Source, on_delete=models.SET_NULL, null=True)
    desc = models.CharField(max_length=5000)
    link = models.CharField(max_length=2000)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True)
    catdict = models.CharField(max_length=5000, default="{}")
    skip_list = models.CharField(max_length=2000, default="[]")

    def __str__(self):
        return self.link or ''


# User-defined custom Topics

class Topic(models.Model):
    title = models.CharField(max_length=100)
    keywords = models.CharField(max_length=5000)
    items = models.ManyToManyField(Item, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, related_name='topics')
    categories = models.ManyToManyField(Category, blank=True)
    numitems = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return str(self.title) or ''

    def get_absolute_url(self):
        return reverse('topicedit', args=[int(self.pk)])

    def get_delete_url(self):
        return reverse('topicdelete', args=[int(self.pk)])


# User's custom email schedule

class EmailSend(models.Model):
    day = models.SmallIntegerField()
    time = models.CharField(max_length=10)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.day) + " " + str(self.time)

# User profile

class Profile(models.Model):

    def defaultsources():
        return Source.objects.filter(default=True)

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    sources = models.ManyToManyField(Source, blank=True, default=defaultsources)
    #                               default=default_sources
    categories = models.ManyToManyField(Category, blank=True)
    topics = models.ManyToManyField(Topic, blank=True)
    stocks = models.CharField(max_length=300, blank=True, default="['DIA', 'SPY', 'QQQ']")
    catorder = models.CharField(max_length=1000, blank=True, default="['Politics', 'International', 'Custom alerts', 'Business']")
    timezone = models.CharField(max_length=40, null=True, choices=TIMEZONES, default='US/Pacific')
    weathercities = models.CharField(max_length=150, default="['Portland, OR']")
    email_confirmed = models.BooleanField(default=False)
    emailformdata = models.CharField(max_length=400, default="[{}]")
    firstemail = models.BooleanField(default=True)

    def __str__(self):
        return str(self.user)

@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()

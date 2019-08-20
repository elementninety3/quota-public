from django.contrib import admin

from .models import Item, Feed, Category, Source, Profile, Story, Topic, EmailSend, UserStory

admin.site.register(Item)
admin.site.register(Feed)
admin.site.register(Category)
admin.site.register(Source)
admin.site.register(Profile)
admin.site.register(Story)
admin.site.register(Topic)
admin.site.register(EmailSend)
admin.site.register(UserStory)

# Register your models here.

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail, get_connection, EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags

from django.utils import timezone

from ast import literal_eval

import pytz

# from time import mktime, strftime
from datetime import datetime, timedelta

import os

from django.contrib.auth.models import User
from bulletin.models import Item, Feed, Source, Profile, Category, Story, Topic, EmailSend

from bulletin.news_functions import avg_score, suffix, custom_strftime


class Command(BaseCommand):

    help = 'Sends hourly emails to users who are signed up'

    def handle(self, *args, **options):

        sysdate = timezone.now().replace(microsecond=0,second=0,minute=0)
        systime = timezone.now().replace(microsecond=0,second=0,minute=0)

        sysdate = sysdate + timedelta(hours=1)
        systime = systime + timedelta(hours=1)

        weekday = sysdate.date().weekday()

#        utctime = pytz.timezone("UTC")

        print(timezone.now())

        items_to_send = EmailSend.objects.filter(day=weekday).filter(time=str(systime.time()))

        print(items_to_send)

        print(timezone.now())

        emails_to_send = []

        for item in items_to_send:

                # Building news data based on user's category preferences

            user = item.user

            me = User.objects.get(username="nathan")

            if user == me:
                print("Admin email skipped")
                continue

            tz = str(user.profile.timezone)

            tzformat = pytz.timezone(tz)

            tz_name = tzformat.tzname(datetime.now())

            date = sysdate.astimezone(tzformat)
            # .replace(microsecond=0,second=0,minute=0,hour=0)
            time = systime.astimezone(tzformat)

            print(date.date(), " ", time.time(), " ", tz_name)

            # naturaldate = (date.strftime("%A, %B %-d, %-I %p") + " " + tz_name)

            naturaldate = (custom_strftime("%A, %B {S}, %-I %p",date) + " " + tz_name)

            datetitle = (custom_strftime("%B {S}, %Y, %-I %p",date) + " " + tz_name)

            datestring = str(date.date())

            try:
                message = open(os.path.expanduser(f'~/bulletyn/news/bulletin/messages/{datestring}.txt'), 'r').read()
            except:
                message = ""

            if user.profile.firstemail == True:
                message = open(os.path.expanduser(f'~/bulletyn/news/bulletin/messages/first_email.txt'), 'r').read()
                user.profile.firstemail = False
                user.profile.save()

            catlist = literal_eval(user.profile.catorder)

            newformat = []

            for cat in catlist:

                # Get all items for category (and max item score for the category)

                try:

                    category = Category.objects.get(category=cat)

                except:

                    newformat.append("Custom alerts")

                    continue

                itemscore_factor = category.story_itemscore_factor
                keywords_factor = category.story_keywords_factor
                numitems_factor = category.story_numitems_factor
                tracker_factor = category.story_tracker_factor
                sources_factor = category.story_sources_factor

                try:
                    usersources = user.profile.sources.all()
                except AttributeError:
                    usersources = Source.objects.all()

                items = Item.objects.filter(category=category).filter(newsource__in=usersources)

                print("Number of items in set: ", len(items))

        #        maxitem = Item.objects.filter(category=category).latest('score')

                try:
                    maxitem = items.latest('score')
                except:
                    maxitem = items.first()

                # Rank stories to show by the number of keywords and the number of items for each

                stories = {}

                allstories = Story.objects.filter(category=category).filter(numitems__gte=4)

                if len(allstories) == 0:
                    allstories = Story.objects.filter(category=category)

                storyitems = {}

                for story in allstories:
                    number_of_items = len(items.filter(story=story))
                    storyitems[story] = number_of_items

                proper_stories = [k for k,v in storyitems.items() if v >= 4]

                if len(proper_stories) == 0:
                    proper_stories = [k for k,v in storyitems.items() if v >= 1]

                for story in proper_stories:
                    storyitems = list(items.filter(story=story).order_by('-score'))[:4]

                    sourcelist = [item.source for item in storyitems]
                    uniquesources = list(dict.fromkeys(sourcelist))

                    rawscore = (float(avg_score(storyitems))/float(maxitem.score)*itemscore_factor + len(literal_eval(story.keywords))**keywords_factor + float(story.numitems)/len(items)*numitems_factor) - (float(story.tracker)*tracker_factor)

                    storyscore = rawscore * (len(uniquesources)/sources_factor)

                    story.score = storyscore
                    story.save()

                    stories[story] = storyscore

                rawstorylist = list(sorted(stories, key=stories.get, reverse=True))

                print("Original story list:")
                for story in rawstorylist:
                    print(story.keywords)

                catstories = []
                latestories = []

                for story in rawstorylist:
                    testkeys = literal_eval(story.keywords)
                    issubset = False

                    for prevstory in catstories:
                        comparekeys = literal_eval(prevstory.keywords)
                        if set(testkeys).issubset(set(comparekeys)) or set(comparekeys).issubset(set(testkeys)):
                            issubset = True

                    if issubset:
                        latestories.append(story)
                    else:
                        catstories.append(story)

                for story in latestories:
                    catstories.append(story)

                print("Final story list:")
                for story in catstories:
                    print(story.keywords)

                catstories = catstories[:4]

                print("Stories ranked and sorted")


                # Now assign the same values for all remaining 'secondary' stories

                sec_story_list = []


                for story in catstories:

                    storyitems = list(items.filter(story=story).order_by('-score'))


                    leadstory = storyitems.pop(0)

                    sublist = []
                    sublist.append(leadstory)  #!!!

                    storyitems = storyitems[:3]
                    sublist.append(storyitems)

                    sec_story_list.append(sublist)

                # Build list of lists to populate the html doc

                if(len(sec_story_list)) > 0:
                    print("Story list added")
                    newformat.append(sec_story_list)
                else:
                    print("Cat name added")
                    newformat.append(cat)


            # Get user's custom topics

            topiclist = Topic.objects.filter(user=user).order_by('-numitems')


            subject, from_email, to = f'Daily Quota: {naturaldate}', 'Quota <news@quotanews.com>', user.email

            html_content = render_to_string('email/news_email.html', {'newformat': newformat, 'topiclist': topiclist, 'date': date.date(), 'time': time.time(), 'tzone': tz, 'tz_name': tz_name, 'message': message, 'datetitle': datetitle}) # render with dynamic value
            text_content = strip_tags(html_content) # Strip the html tag. So people can see the pure text at least.

            # create the email, and attach the HTML version as well.
            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            # msg.content_subtype = "html"

            emails_to_send.append(msg)

            # msg.send()
            print(f'Message sent to {to} added to queue')
            print(timezone.now())
#
#            else:
#                continue

        connection = get_connection()
        connection.send_messages(emails_to_send)
        print("Emails sent")
        print(timezone.now())

# Django imports

from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.urls import reverse

from django.views import generic
from django.contrib import messages
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required

from django.utils import timezone

# Email verification imports

from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_text, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from .tokens import account_activation_token
from django.template.loader import render_to_string
from django.utils.html import strip_tags

# For email feedback

from django.core.mail import EmailMessage, EmailMultiAlternatives

# Bulletin news imports

from time import mktime, strftime, strptime
from datetime import datetime, timedelta
import calendar

from operator import or_
from django.db.models import Q, Max

import string

import os

import pytz

from ast import literal_eval

# Widget imports

from iexfinance.stocks import Stock

from forecastio import load_forecast
from geopy.geocoders import Nominatim

# Local imports

from .forms import StockPreferenceForm, NewTopicForm, CategoryOrderForm, SelectForm, TimezoneForm, SignupForm, WeatherForm, EmailTimeForm, SetAddressForm, EmailForm, EmailFormset, SourcePreferenceForm, AllSourceForm, TopicForm, KeywordFormset, WidgetForm, ContactForm

from .models import Item, Feed, Source, Profile, Category, Story, Topic, EmailSend
from django.contrib.auth.models import User

from .news_functions import key_count, key_list_count, word_count, key_compare, regex_count_occurrences, topic_count, avg_score, google_lat_lng



# Main bulletin view calcs


def newindex(request):

    # Getting user's timezone info to display in header

    user = request.user

    try:
        tz = str(user.profile.timezone)
    except:
        tz = "US/Eastern"

    print(tz)

    # Calculating current date and time

    tzformat = pytz.timezone(tz)

    tz_name = tzformat.tzname(datetime.now())

    print(timezone.now())

    usertz = timezone.now().astimezone(tzformat)

    print(usertz)

    date = usertz.replace(microsecond=0,second=0,minute=0,hour=0)
    time = usertz.replace(microsecond=0,second=0,minute=0)

    print(date.time(), " ", time.time())


    print("Starting to build data")


    # Building news data based on user's category preferences

    try:
        catlist = literal_eval(user.profile.catorder)
    except:
        catlist = ["Politics", "Business", "International", "Sports", "Custom alerts"]

    newformat = []

    for cat in catlist:
        print(cat)

        # Get all items for category (and max item score for the category)

        try:

            category = Category.objects.get(category=cat)

        except:

            newformat.append("Custom alerts")

            continue

        # Get ranking factors for each category

        itemscore_factor = category.story_itemscore_factor
        keywords_factor = category.story_keywords_factor
        numitems_factor = category.story_numitems_factor
        tracker_factor = category.story_tracker_factor
        sources_factor = category.story_sources_factor

        # Filter to list of total items based on user's sources

        try:
            usersources = user.profile.sources.all()
        except AttributeError:
            usersources = Source.objects.filter(default=True)

        print("Getting items")

        items = Item.objects.filter(category=category).filter(newsource__in=usersources)

        print("Number of items in set: ", len(items))

#        maxitem = Item.objects.filter(category=category).latest('score')

        # How to fix this issue ??

        try:
            maxitem = items.latest('score')
        except:
            maxitem = items.first()

        # Rank stories to show by the number of keywords and the number of items for each

        print("Ranking stories")

        stories = {}

        allstories = Story.objects.filter(category=category).filter(numitems__gte=4).filter(new_story=False)

        if len(allstories) < 4:
            allstories = Story.objects.filter(category=category).filter(new_story=False)

        storyitems = {}

        for story in allstories:
            number_of_items = len(items.filter(story=story))
            storyitems[story] = number_of_items

        proper_stories = [k for k,v in storyitems.items() if v >= 4]

        if len(proper_stories) < 2:
            proper_stories = [k for k,v in storyitems.items() if v >= 1]

        for story in proper_stories:
            storyitems = list(items.filter(story=story).order_by('-score'))[:4]

            sourcelist = [item.source for item in storyitems]
            uniquesources = list(dict.fromkeys(sourcelist))

            try:
                rawscore = (float(avg_score(storyitems))/float(maxitem.score)*itemscore_factor + len(literal_eval(story.keywords))**keywords_factor + float(story.numitems)/len(items)*numitems_factor) - (float(story.tracker)*tracker_factor)
            except ZeroDivisionError:
                rawscore = 1

            storyscore = rawscore * (len(uniquesources)/sources_factor)

            story.score = storyscore
            story.save()

            stories[story] = storyscore

        rawstorylist = list(sorted(stories, key=stories.get, reverse=True))

        print("Original story list:")
        for story in rawstorylist:
            print(story.keywords)

        # Move stories down the list if they overlap with stories above them

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

        # Now determine which items should go with what stories

        sec_story_list = []

        print("Assigning items to stories")

        for story in catstories:

            storyitems = list(items.filter(story=story).order_by('-score'))

#            try:

            leadstory = storyitems.pop(0)

            # Replacing story image if one wasn't available

            if leadstory.top_image == '':
                for item in storyitems[:3]:
                    if item.top_image != '':
                        leadstory.top_image = item.top_image
                        leadstory.source = item.source
                        leadstory.save()
                        break

            sublist = []
            sublist.append(leadstory)  #!!!

            storyitems = storyitems[:3]
            sublist.append(storyitems)

            sec_story_list.append(sublist)

        # Build list of lists to populate the html doc

#            cat_story_list.append(sec_story_list)

        print(cat,": ",sec_story_list)

        if(len(sec_story_list)) > 0:
            print("Story list added")
            newformat.append(sec_story_list)
        else:
            print("Cat name added")
            newformat.append(cat)

#        except:
#
#            newformat.append("Custom topics")
#
#            continue

    # from pprint import pprint

    # pprint(newformat)

    # Get user's custom topics

    try:
        topiclist = Topic.objects.filter(user=user).order_by('-numitems')
    except:
        topiclist = []

    # Populate widget data

    print("Populating widgets")

    # Get user's stocks
    try:
        stocklist = literal_eval(user.profile.stocks)
    except:
        print("Couldn't get stock list")
        stocklist = ["DIA", "SPY", "SVXY"]

    stockrange = int(len(stocklist))

    # Get the data for each stock and populate a list
    stockprices = []

    try:
        for i in stocklist:
            result = {}
            data = Stock(i,token=os.getenv('STOCK_KEY')).get_quote()
            print("Got stock quote")
            result['name'] = data['companyName']
            result['ticker'] = i
            if data['iexRealtimePrice'] is None:
                result['price'] = data['latestPrice']
            else:
                result['price'] = data['iexRealtimePrice']
            result['close'] = data['previousClose']
            result['change'] = result['price'] - result['close']
            result['pctchange'] = result['change']/result['close']*100
            if result['change'] < 0:
                result['neg'] = 1
            else:
                result['neg'] = 0
            result['price'] = '{:.2f}'.format(result['price'])
            result['change'] = '{:.2f}'.format(result['change'])
            result['pctchange'] = '{:.2f}'.format(result['pctchange'])
            stockprices.append(result)
            print(f"Added data for {i}")

    except:
        stockprices = []
        print("Couldn't get stock prices")

    stocksmall = stockprices[:3]

    # Weather widget

    # Get user's cities for weather

    try:
        weathercities = literal_eval(user.profile.weathercities)
        print("Got user's cities")
    except:
        weathercities = ["Portland, OR"]

    print("Got user's cities")
    print(weathercities)

    # For each city, get the weather data

    locations = []
    locationdict = {}

    api_key = os.getenv('WEATHER_KEY')

    geolocator = Nominatim(user_agent="quotanews")
    geosuccess = True

    for city in weathercities:
        try:
            location = geolocator.geocode(city)
            print(city," - ",location)
            locations.append(location)
            locationdict[city] = location
        except:
            print("Location for ",city," not found")
            geosuccess = False

    print("Got locations")
    print(locationdict)

    weather = []
    weathersmall = []

    if geosuccess:
        # for i, location in zip(range(len(locations)), locations):
        for i, location in locationdict.items():

            # Get the weather
            print("Doing the forecast for ",i)

            forecast = load_forecast(api_key, location.latitude, location.longitude)
            daily_forecast = forecast.daily().data

            print("Got weather data for ",i)

            # Unpack daily weather and assign data into list of dicts

            cityweather = []

            for index, day in zip(range(5), daily_forecast):
                result = {}
                result['city'] = i
                result['time'] = day.time
                result['high'] = round(day.temperatureHigh)
                result['low'] = round(day.temperatureLow)
                result['icon'] = day.icon
                result['day'] = day.time.strftime('%a')

                # Create daily summary

                summ = day.icon.split("-")[0:2]

                if summ[0]=="clear":
                    summ=["clear"]

                summary = str(" ".join(summ))

                if summary == "partly cloudy":
                    summary = "P. cloudy"
                    result['summary'] = summary
                else:
                    result['summary'] = summary.capitalize()

                cityweather.append(result)

            cityweathersmall = cityweather[:3]

            weather.append(cityweather)
            weathersmall.append(cityweathersmall)

        print("Got weather dict through Nominatim")
        print(weather)

        weathersmall = weathersmall[:1]

    else:
        for city in weathercities:
            lat, lng = google_lat_lng(os.getenv('GOOGLE_KEY'),city)

            forecast = load_forecast(api_key,lat,lng)
            daily_forecast = forecast.daily().data

            cityweather = []

            for index, day in zip(range(5), daily_forecast):
                result = {}
                result['city'] = city
                result['time'] = day.time
                result['high'] = round(day.temperatureHigh)
                result['low'] = round(day.temperatureLow)
                result['icon'] = day.icon
                result['day'] = day.time.strftime('%a')

                # Create daily summary

                summ = day.icon.split("-")[0:2]

                if summ[0]=="clear":
                    summ=["clear"]

                summary = str(" ".join(summ))

                if summary == "partly cloudy":
                    summary = "P. cloudy"
                    result['summary'] = summary
                else:
                    result['summary'] = summary.capitalize()

                cityweather.append(result)

            cityweathersmall = cityweather[:3]

            weather.append(cityweather)
            weathersmall.append(cityweathersmall)

        print("Got weather dict through Google")
        print(weather)

        weathersmall = weathersmall[:1]


    # Set required context variables

    print("Done")

    context = {'newformat': newformat, 'topiclist': topiclist, 'stockprices': stockprices, 'stockpricessmall': stocksmall, 'range': range(stockrange), 'weather': weather, 'weathersmall': weathersmall, 'date': date, 'time': time, 'tzone': tz, 'tz_name': tz_name}

    return render(request, 'bulletin/newindex.html', context)



@login_required
def topicview(request):


    # Get user's timezone information

    user = request.user

    try:
        tz = str(user.profile.timezone)
    except:
        tz = "US/Eastern"

    # Set date and time

    tzformat = pytz.timezone(tz)

    tz_name = tzformat.tzname(datetime.now())

    usertz = timezone.now().astimezone(tzformat)

    date = usertz.replace(microsecond=0,second=0,minute=0,hour=0)
    time = usertz.replace(microsecond=0,second=0,minute=0)


    # Get user's topics, ordered by number of items - if they don't have any, send them home

    topiclist = Topic.objects.filter(user=user).order_by('-numitems')

    if len(topiclist) == 0:
        return HttpResponseRedirect(reverse('index'))

    # Populate topics with items

    topicformat = []

    for topic in topiclist:

        itemscores = {}

        itemlist = Item.objects.filter(category__in=topic.categories.all()).filter(newsource__in=user.profile.sources.all())

        for item in itemlist:

            searchtext = (item.title + " " + item.desc)
            #splitsearch = searchtext.split(" ")

            topic_counter = 0

            for topickey in literal_eval(topic.keywords):

                counter = 0

                counter = regex_count_occurrences(searchtext,topickey)

#                for word in splitsearch:
#
#                    if word == topic.lower():
#                        counter +=1
#                    else:
#                        counter = counter

            topic_counter += counter

            if topic_counter > 0:
                itemscores[item] = topic_counter

        topicallitems = list(sorted(itemscores, key=itemscores.get, reverse=True))

        topictopitems = []
        topicstories = []

        for item in topicallitems:
            if len(topicstories)>3:
                break

            if item.story in topicstories:
                continue
            else:
                topictopitems.append(item)
                topicstories.append(item.story)

        # storyranks = {}
        storyitemdict = {}

        for story, i in zip(topicstories,range(len(topictopitems))):
            storyitems = []
            storyitems.append(topictopitems[i])

            additional_storyitems = list(itemlist.filter(story=story).order_by('-score'))[:4]
            for item in additional_storyitems:
                if len(storyitems)>3:
                    continue
                elif item in storyitems:
                    continue
                else:
                    storyitems.append(item)

            storyitemdict[story] = storyitems

            # storyranks[story] = storyitems[0].score

        # stories_ranked = list(sorted(storyranks, key=storyranks.get, reverse=True)[:4])

        story_item_list = []

        # for story in stories_ranked:
        for story in topicstories:

            storyitems = storyitemdict[story]

            leadstory = storyitems.pop(0)

            sublist = []
            sublist.append(leadstory)

            storyitems = storyitems[:3]
            sublist.append(storyitems)

            story_item_list.append(sublist)

        topicformat.append(story_item_list)

    return render(request, 'bulletin/topicview.html', {'usertopics': topiclist, 'topicformat':topicformat, 'topiczip':zip(topicformat,topiclist), 'date': date, 'time': time, 'tzone': tz, 'tz_name': tz_name})


@login_required
def preferences(request):
    user = request.user

    # Process any data posted to server

    if request.method == 'POST':
        form = TimezoneForm(request.POST)
        if form.is_valid():
            tz = form.cleaned_data['timezone']
            user = request.user
            user.profile.timezone = tz
            user.profile.save()
            # do nothing else for now
            messages.success(request, 'Timezone updated successfully.')
            return HttpResponseRedirect(reverse('preferences'))

    # Otherwise, create blank copies of all the forms for preferences

    else:
        # Timezone form
        tzform = TimezoneForm(initial={'timezone':user.profile.timezone})

        # Email address form

        addressform = SetAddressForm(initial={'email':user.email})

        # Cat order form

        usercats = literal_eval(user.profile.catorder)
        totalcats = list(Category.objects.all())

        # Get list of other categories (that user hasn't already selected)

        othercats = [x for x in totalcats if x.category not in usercats]

        # Build list with user's categories in order at the top, followed by remaining choices

        choicelist = []
        for cat in usercats:
            adder = (cat,cat)
            choicelist.append(adder)

        for cat in othercats:
            adder = (cat.category,cat.category)
            choicelist.append(adder)

        if ("Custom alerts","Custom alerts") not in choicelist:
            choicelist.append(("Custom alerts", "Custom alerts"))

        catform = SelectForm(choicelist,initial={'categories':usercats})

        # Email times form
        utcvals = literal_eval(user.profile.emailformdata) #!!!

        initialvals = []

        usertz = pytz.timezone(str(user.profile.timezone))
        utctz = pytz.timezone("UTC")
        daystr = str(timezone.now().date())
        strdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

        # Convert between time values and format to store on the server

        try:
            for item in utcvals:
                rowdata = {}

                dtstr = daystr + " " + str(item['time'])
                naivetime = datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")
                utctime = utctz.localize(naivetime)
                usertime = utctime.astimezone(usertz)

                naiveround = usertime.replace(microsecond=0, second=0, minute=0, hour=0, tzinfo=None)
                utcround = utctime.replace(microsecond=0, second=0, minute=0, hour=0, tzinfo=None)
                delta = utcround - naiveround

                daydiff = delta.days

                if item['day'] == "Weekdays":
                    rowdata['day'] = item['day']
                    rowdata['time'] = str(usertime.time())

                elif item['day'] == "Every day":
                    rowdata['day'] = item['day']
                    rowdata['time'] = str(usertime.time())

                elif int(item['day']) in range(7):

                    try:
                        daycode = item['day'] - daydiff
                    except:
                        daycode = 0

                    rowdata['day'] = strdays[daycode]
                    rowdata['time'] = str(usertime.time())

                initialvals.append(rowdata)
        except KeyError:
            initialvals = [{}]

        formset = EmailFormset(initial=initialvals)


    return render(request, 'bulletin/preferences.html', {'tzform': tzform, 'formset': formset, 'catform': catform, 'addressform': addressform})


# Widget preferences
@login_required
def widgetprefs(request):

    # Get user's current preferences

    user = request.user
    currstocks = literal_eval(user.profile.stocks)
    currcities = literal_eval(user.profile.weathercities)

    # Populate total list of options for cities

    citylist = []
    rawcities = open(os.path.expanduser('~/bulletyn/news/bulletin/weathercities.txt'), 'r').read().splitlines()

    intermediate = []

    for city in rawcities:
        newformat = city[1:][:-1]
        intermediate.append(newformat)

    for city in currcities:
        newtuple = (city,city)
        citylist.append(newtuple)

    for city in intermediate:  #rawcities
        if city not in currcities:
            newtuple = (city,city)
            citylist.append(newtuple)

    # Populate total list of options for stocks

    tickerlist = open(os.path.expanduser('~/bulletyn/news/bulletin/tickerlist.txt'), 'r').read().splitlines()
    stocknames = open(os.path.expanduser('~/bulletyn/news/bulletin/stocklist.txt'), 'r').read().splitlines()

    rawstocks = {}

    for i in range(len(tickerlist)):
        rawstocks[tickerlist[i]] = stocknames[i]

    stocklist = []

    # rawstocks = {"AAPL":"Apple, Inc. (AAPL)", "JCP":"JC Penney, Inc. (JCP)", "NKE":"Nike, Inc. (NKE)", "TSLA":"Tesla, Inc. (TSLA)"}

    for stock in currstocks:
        newtuple = (stock,rawstocks[stock])
        stocklist.append(newtuple)

    for stock in rawstocks:
        if stock not in currstocks:
            newtuple = (stock,rawstocks[stock])
            stocklist.append(newtuple)


    # Process any data posted to the server

    if request.method == 'POST':
        stockform = WidgetForm('stock',stocklist,request.POST)
        weatherform = WidgetForm('city',citylist,request.POST)
        print(request.POST)

        stockpost = request.POST.get("stocksempty", "")
        weatherpost = request.POST.get("weatherempty", "")

        # Check whether the stock data or the weather data was submitted

        if stockpost == "submitted":
            try:
                raw_list = list(request.POST.getlist("selectedchoices[]"))
                ns_list = []

                for stockname in raw_list:
                    inter = stockname[:-1]
                    ticker = inter.partition("(")[2]
                    ns_list.append(ticker)

                user.profile.stocks = ns_list
                user.profile.save()
                messages.success(request, 'Stock preferences updated successfully.')
            except:
                messages.error(request, 'An error occured. Please try again.')

        elif weatherpost == "submitted":
            try:
                nc_list = request.POST.getlist("selectedchoices[]")
                user.profile.weathercities = list(nc_list)
                user.profile.save()
                messages.success(request, 'Weather preferences updated successfully.')
            except:
                messages.error(request, 'An error occured. Please try again.')

        return HttpResponseRedirect(reverse('widgetprefs'))

    # If nothing has been submitted, populate blank copies of the forms

    else:

        stockform = WidgetForm('stock',stocklist,initial={'stock':currstocks})
        weatherform = WidgetForm('city',citylist,initial={'city':currcities})

        context = {'stockform': stockform, 'weatherform': weatherform}

        return render(request, 'bulletin/widget-preferences.html', context)


# Topic preferences
@login_required
def topicprefs(request):

    # Give a warning if they don't have custom topics selected in their category preferences

    if "Custom alerts" in literal_eval(request.user.profile.catorder):
        topicwarn = False
    else:
        topicwarn = True

    # Process any data posted to the server

    if request.method == 'POST':
        topicform = TopicForm(request.POST)
        keywordformset = KeywordFormset(request.POST)


        if topicform.is_valid() and keywordformset.is_valid():
            newtitle = topicform.cleaned_data['title']
            cats = topicform.cleaned_data['categories']
            user = request.user

            keyslist = []

            for form in keywordformset:
                print(form.cleaned_data)
                try:
                    if form.cleaned_data['DELETE']:
                        continue
                    else:
                        keyword = form.cleaned_data['keyword']
                except KeyError:
                    continue

                keyslist.append(keyword)

            print(keyslist)

            NewTopic = Topic(title=newtitle,keywords=keyslist,user=user)
            NewTopic.save()
            NewTopic.categories.set(cats)
            NewTopic.save()

            messages.success(request, f'New alert "{newtitle}" created.')

            return HttpResponseRedirect(reverse('topicprefs'))

        # If the user hasn't filled out everything, tell them what they need to change

        else:
            print("Title: ",topicform['title'].errors)
            print("Categories: ",topicform['categories'].errors)

            if topicform.is_valid():
                messages.error(request, 'Please enter at least one keyword for your alert.')
                return HttpResponseRedirect(reverse('topicprefs'))
            elif topicform['categories'].errors:
                messages.error(request, 'Please select at least one category to search for your alert.')
                return HttpResponseRedirect(reverse('topicprefs'))
            elif topicform['title'].errors:
                messages.error(request, 'Please enter a title for your alert.')
                return HttpResponseRedirect(reverse('topicprefs'))
            else:
                messages.error(request, 'An error occured.')
                return HttpResponseRedirect(reverse('topicprefs'))

    # Render page

    user = request.user
    usertopics = Topic.objects.filter(user=user)
    form = TopicForm(initial={'categories':Category.objects.all()})
    formset = KeywordFormset(initial=[{}])

    context = {'form': form, 'formset':formset, 'usertopics': usertopics, 'topicwarn': topicwarn}

    return render(request, 'bulletin/topic-preferences.html', context)

# Topic edit
@login_required
def topicedit(request, topic_id):

    # Get topic to edit

    topic_edit = get_object_or_404(Topic, pk=topic_id)

    # Warn user if they don't have custom topics selected as a category

    if "Custom alerts" in literal_eval(request.user.profile.catorder):
        topicwarn = False
    else:
        topicwarn = True


    # Check that this user is authorized to edit this topic

    if topic_edit.user == request.user:

        # If they've posted changes to the server, save them

        if request.method == 'POST':
            topicform = TopicForm(request.POST)
            keywordformset = KeywordFormset(request.POST)

            if topicform.is_valid() and keywordformset.is_valid():
                newtitle = topicform.cleaned_data['title']
                cats = topicform.cleaned_data['categories']
                user = request.user

                keyslist = []

                for form in keywordformset:
                    try:
                        if form.cleaned_data['DELETE']:
                            continue
                        else:
                            keyword = form.cleaned_data['keyword']
                    except KeyError:
                        continue

                    keyslist.append(keyword)

                topic_edit.title = newtitle
                topic_edit.keywords = keyslist
                topic_edit.categories.set(cats)
                topic_edit.save()

                messages.success(request, f'Alert "{newtitle}" saved.')

                return HttpResponseRedirect(reverse('topicprefs'))

            # If the user didn't fill everything out, tell them what they are missing

            else:
                print("Title: ",topicform['title'].errors)
                print("Categories: ",topicform['categories'].errors)

                if topicform.is_valid():
                    messages.error(request, 'Please enter at least one keyword for your alert.')
                    return HttpResponseRedirect(reverse('topicprefs'))
                elif topicform['categories'].errors:
                    messages.error(request, 'Please select at least one category to search for your alert.')
                    return HttpResponseRedirect(reverse('topicprefs'))
                elif topicform['title'].errors:
                    messages.error(request, 'Please enter a title for your alert.')
                    return HttpResponseRedirect(reverse('topicprefs'))
                else:
                    messages.error(request, 'An error occured.')
                    return HttpResponseRedirect(reverse('topicprefs'))

            return HttpResponseRedirect(reverse('topicprefs'))

        # Otherwise, populate the template with data from the topic the user is editing

        else:
            user = request.user
            usertopics = Topic.objects.filter(user=user)

            initialkeys = []
            for key in literal_eval(topic_edit.keywords):
                newdict = {}
                newdict['keyword'] = key
                initialkeys.append(newdict)

            form = TopicForm(initial={'title':topic_edit.title,'categories':topic_edit.categories.all()})
            formset = KeywordFormset(initial=initialkeys)

            context = {'form': form, 'formset':formset, 'usertopics': usertopics, 'topicwarn': topicwarn}

            return render(request, 'bulletin/topic-preferences.html', context)

    else:

        return HttpResponseRedirect(reverse('topicprefs'))

# Topic delete
@login_required
def topicdelete(request, topic_id):

    # Get the topic the user wants to delete

    topic_delete = get_object_or_404(Topic, pk=topic_id)

    # Make sure the user has authority to delete this topic

    if topic_delete.user == request.user:

        # If they've posted the topic to delete, go ahead and delete it

        if request.method == 'POST':
            topic_title = topic_delete.title
            topic_delete.delete()

            messages.success(request, f'Alert "{topic_title}" deleted.')

            return HttpResponseRedirect(reverse('topicprefs'))

        # Otherwise, show them the confirmation page

        else:
            keyslist = literal_eval(topic_delete.keywords)

            return render(request, 'bulletin/topic-delete.html', {'topic_delete':topic_delete, 'keyslist':keyslist})

    # If they don't have the authority, send them to the topic preferences page
    else:
        user = request.user

        if "Custom alerts" in literal_eval(request.user.profile.catorder):
            topicwarn = False
        else:
            topicwarn = True

        usertopics = Topic.objects.filter(user=user)
        form = TopicForm(initial={'categories':Category.objects.all()})
        formset = KeywordFormset()

        context = {'form': form, 'formset':formset, 'usertopics': usertopics, 'topicwarn': topicwarn}

        return render(request, 'bulletin/topic-preferences.html', context)

# Category order preferences
@login_required
def catorder(request):

    # Get user's current category order

    user = request.user
    usercats = literal_eval(user.profile.catorder)
    totalcats = list(Category.objects.all())

    # Get list of other categories (that user hasn't already selected)

    othercats = [x for x in totalcats if x.category not in usercats]

    # Build list with user's categories in order at the top, followed by remaining choices

    choicelist = []
    for cat in usercats:
        adder = (cat,cat)
        choicelist.append(adder)

    for cat in othercats:
        adder = (cat.category,cat.category)
        choicelist.append(adder)

    if ("Custom alerts","Custom alerts") not in choicelist:
        choicelist.append(("Custom alerts", "Custom alerts"))

    # If form is being submitted...save the new order to the user's profile

    if request.method == 'POST':
        form = SelectForm(choicelist,request.POST)
        if form.is_valid():
            catorder = list(form.cleaned_data['categories'])
            user.profile.catorder = catorder

            # Also need to assign the categories to the user the proper way through ForeignKey

            newcats = []
            for cat in catorder:
                try:
                    newcat = Category.objects.get(category=cat)
                    newcats.append(newcat)
                except:
                    continue

            user.profile.categories.set(newcats)
            user.profile.save()

            messages.success(request, 'Category preferences updated successfully.')

            return HttpResponseRedirect(reverse('preferences'))

        # If they don't select anything, tell them they have to select at least one thing

        else:
            messages.error(request, 'You must select at least one news category.')
            return HttpResponseRedirect(reverse('preferences'))

    # If someone tries to go to this url, just give them the proper preferences view

    return HttpResponseRedirect(reverse('preferences'))

# Email preferences
@login_required
def emailprefs(request):

    user = request.user

    # Set some variables to use here

    days = dict(zip(calendar.day_name, range(7)));
    strdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday']

    # If they're submitting their preferences, save them

    if request.method == 'POST':
        formset = EmailFormset(request.POST)

        if formset.is_valid():

            # Delete all of the user's current email instances

            print("Formset data")
            for form in formset:
                print(form.cleaned_data)
            useremails = EmailSend.objects.filter(user=user)
            for i in useremails:
                i.delete()

            # Build the dataset we need form the submitted for data

            userformdata = []

            for form in formset:

                # Get each form's data to save to the profile

                formdata = {}
                try:
                    if form.cleaned_data['DELETE']:
                        continue
                    else:
                        day = form.cleaned_data['day']
                        time = form.cleaned_data['time']
                except KeyError:
                    continue

                # Convert whatever the user selected in their timezone to UTC (including day difference if applicable)

                daystr = str(timezone.now().date())
                dtstr = daystr + " " + time
                usertz = pytz.timezone(str(user.profile.timezone))
                naivetime = datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")
                awaretime = usertz.localize(naivetime)

                utctz = pytz.timezone("UTC")

                utctime = awaretime.astimezone(utctz)

                naiveround = naivetime.replace(microsecond=0, second=0, minute=0, hour=0, tzinfo=None)
                utcround = utctime.replace(microsecond=0, second=0, minute=0, hour=0, tzinfo=None)
                delta = utcround - naiveround

                daydiff = delta.days

                # Now create a new email instance for each form item...

                if day in list(days.keys()):

                    adjusted_day = days[day]+daydiff
                    if adjusted_day == 7:
                        adjusted_day = 0

                    formdata['day'] = adjusted_day
                    formdata['time'] = str(utctime.time())

                    newemail = EmailSend(day=adjusted_day,time=str(utctime.time()),user=user)
                    newemail.save()

                # If they selected a multiple-day email, we have to create several objects instead

                elif day == 'Every day':
                    for i in strdays:
                        newemail = EmailSend(day=days[i],time=str(utctime.time()),user=user)
                        newemail.save()

                        formdata['day'] = 'Every day'
                        formdata['time'] = str(utctime.time())

                elif day == 'Weekdays':
                    for i in weekdays:
                        newemail = EmailSend(day=days[i]+daydiff,time=str(utctime.time()),user=user)
                        newemail.save()

                        formdata['day'] = 'Weekdays'
                        formdata['time'] = str(utctime.time())

                userformdata.append(formdata)

            # Add the list with form data to the user profile and save it so we can populate the form next time

            user.profile.emailformdata = userformdata
            user.profile.save()

            messages.success(request, 'Email preferences updated successfully.')

            return HttpResponseRedirect(reverse('preferences'))

    else:

        # Otherwise all we have to do is give the user the preferences page

        # formset = EmailFormset()

        return HttpResponseRedirect(reverse('preferences'))


    return HttpResponseRedirect(reverse('preferences'))


# Source preferences
@login_required
def sourceprefs(request):

    # If the user is saving preferences, update their preferences

    if request.method == 'POST':
        sourceform = AllSourceForm(request.POST)

        if sourceform.is_valid():
            newsources = sourceform.cleaned_data['sources']
            request.user.profile.sources.set(newsources)
            request.user.profile.save()

            messages.success(request, 'Source preferences updated successfully.')

            return HttpResponseRedirect(reverse('sourceprefs'))

    # Otherwise, we have to define the available sources for them to choose from for each cateogry

    else:

        # Get list of user's categories (so they know what matters when they're picking sources)

        usercats = literal_eval(request.user.profile.catorder)

        if "Custom alerts" in usercats:
            usercats.remove("Custom alerts")

        totalcats = list(Category.objects.all())

        usersources = request.user.profile.sources

        # Get list of other categories (that user hasn't already selected) so they can see everything

        othercats = [x for x in totalcats if x.category not in usercats]
        print(othercats)

        # Build list with user's categories in order at the top, followed by remaining choices

        choicelist = []
        for cat in usercats:
            adder = Category.objects.get(category=cat)
            choicelist.append(adder)


        # Now we need to create a form for each of those categories

        formlist = []

        for cat in choicelist:

            # Populate each category's form with the sources each user has already selected for that category

            initial_vals = usersources.filter(category=cat)
            form = SourcePreferenceForm(cat, initial={'sources':initial_vals}, auto_id=f'id_{cat}_%s')
            formlist.append(form)

        # Zip the category and form list for better rendering

        formcatlist = zip(formlist,usercats)

        # Repeat the process for non-user-selected categories

        otherforms = []

        for cat in othercats:
            initial_vals = usersources.filter(category=cat)
            newform = SourcePreferenceForm(cat, initial={'sources':initial_vals}, auto_id=f'id_{cat}_%s')
            otherforms.append(newform)

        formotherlist = zip(otherforms,othercats)

        return render(request, 'bulletin/source-preferences.html', {'formcatlist': formcatlist, 'formotherlist': formotherlist})

# Email address preferences
@login_required
def setaddress(request):

    user = request.user

    # If they're submitting a new email address:

    if request.method == 'POST':
        form = SetAddressForm(request.POST)

        if form.is_valid():
            newemail = form.cleaned_data['email']

            # Check if they didn't change it, because then they don't need to revalidate

            if user.email == newemail:
                messages.success(request, 'Your email address has already been confirmed.')
                return HttpResponseRedirect(reverse('preferences'))

            # If it's a new email address, then update the user's profile, but make them validate it

            else:

                # Update the email but turn the confirmation off

                user.email = newemail
                user.profile.email_confirmed=False
                user.save()

                # Send a verification email so they can revalidate

                current_site = get_current_site(request)
                subject = 'Quota: Verify your email change'
                message = render_to_string('registration/address_change_email.html', {
                    'user': user,
                    'domain': current_site.domain,
                    'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                    'token': account_activation_token.make_token(user),
                })

                user.email_user(subject, message)

                return redirect('activation_sent')

        # If they didn't enter a valid email address, let them know

        else:
            messages.error(request,'Please enter a valid email address.')
            return HttpResponseRedirect(reverse('preferences'))

    return HttpResponseRedirect(reverse('preferences'))


#New user signup
def signup(request):

    # If they already have an account, just kick them to the homepage

    if request.user.is_authenticated:
        return HttpResponseRedirect(reverse('index'))

    # If they're submitting their signup form, create the new user

    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():

            # Create the user
            user = form.save(commit=False)
            user.is_active=False
            user.save()


            # Send them a verification email
            current_site = get_current_site(request)
            subject = 'Quota: Verify your email'

            html_content = render_to_string('registration/account_activation_email.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.pk)).decode(),
                'token': account_activation_token.make_token(user),
            })

            text_content = strip_tags(html_content) # Strip the html tag, so people can see the pure text at least if they don't have HTML email for some reason

            to = user.email
            from_email='Quota <quota@quotanews.com>'

            msg = EmailMultiAlternatives(subject, text_content, from_email, [to])
            msg.attach_alternative(html_content, "text/html")
            # msg.content_subtype = "html"
            msg.send()

            # Add all the default sources to their profile

            user.profile.sources.set(Source.objects.filter(default=True))
            user.profile.save()

            # Send them to a page that lets them know they need to verify their email

            return redirect('activation_sent')

    # Otherwise, just give them a blank copy of the signup form

    else:
        form = SignupForm()
    return render(request, 'signup.html', {'form': form})

# Activation view
def activate(request, uidb64, token):

    #Get the relevant info from the link the user clicked

    #try:
    uid = urlsafe_base64_decode(uidb64).decode()
    user = User.objects.get(pk=uid)
    #except (TypeError, ValueError, OverflowError):  #user.DoesNotExist
    #user = None

    # Assuming everything checks out, log them in and set their account up

    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.profile.email_confirmed = True
        user.save()
        login(request, user)
        return redirect('setup1')

    # Otherwise, tell them they clicked a bad link

    else:
        return render(request, 'registration/activation_invalid.html')

# Activation sent view
def activation_sent(request):

    return render(request, 'registration/activation_sent.html')

# Donation view
def donate(request):
    return render(request, 'bulletin/donate.html')

# Thank you for donating view
def thankyou(request):
    return render(request, 'bulletin/thank-you.html')

# About view
def about(request):
    return render(request, 'bulletin/about.html')

    # Landing page view
def index(request):
    return render(request, 'bulletin/landing.html')

# Feedback view
def feedback(request):
    user = request.user

    # If they're logged in, pre-populate the form with their email address on file

    try:
        useremail = user.email
    except:
        useremail = ""

    # If they're submitting the form, send along their feedback like they want!
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = "Quota feedback"
            feedback = form.cleaned_data['message']
            from_email = form.cleaned_data['email']
            to = "feedback@quotanews.com"

            msg = EmailMessage(subject, feedback, from_email, [to])
            msg.send()

            messages.success(request, 'Thanks for sending us your feedback. Someone will be in touch with you shortly if appropriate.')

        return HttpResponseRedirect(reverse('feedback'))

    # Otherwise, don't just stand there, give them a blank copy of the email form!

    else:
        form = ContactForm(initial={'email': useremail})

        return render(request, 'bulletin/feedback.html', {'form': form})


# Test view of the email system (used in case you don't want to wait for the top of the hour to see your changes)
def emailtest(request):

    sysdate = timezone.now()
    systime = timezone.now().replace(microsecond=0,second=0,minute=0)

    user = request.user

    tz = str(user.profile.timezone)

    tzformat = pytz.timezone(tz)

    tz_name = tzformat.tzname(datetime.now())

    date = sysdate.astimezone(tzformat)
    # .replace(microsecond=0,second=0,minute=0,hour=0)
    time = systime.astimezone(tzformat)

    print(date.date(), " ", time.time(), " ", tz_name)


    datestring = str(date.date())

    try:
        message = open(os.path.expanduser(f'~/bulletyn/news/bulletin/messages/{datestring}.txt'), 'r').read()
    except:
        message = "No message found for today."


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

        maxitem = items.latest('score')

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

        catstories = list(sorted(stories, key=stories.get, reverse=True)[:4])


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

        newformat.append(sec_story_list)


    # Get user's custom topics

    topiclist = Topic.objects.filter(user=user)

    return render(request, 'email/news_email.html', {'newformat': newformat, 'topiclist': topiclist, 'date': date.date(), 'time': time.time(), 'tzone': tz, 'tz_name': tz_name, 'message':message})
    # 'email/news_email_stories.html'


# Unsubscribe view
@login_required
def unsubscribe(request):
    user = request.user

    # Right now they have to be logged in to unsubscribe. Can we make this easier ??
    useremail = user.email

    # If they've submitted their request, then sadly, delete all their email objects
    if request.method == 'POST':
        useremailobjects = EmailSend.objects.filter(user=user)
        for i in useremailobjects:
            i.delete()
        user.profile.emailformdata = "[{}]"
        user.profile.save()

        messages.success(request, f"Unsubscribed from emails to {useremail}.")

        return HttpResponseRedirect(reverse('preferences'))

    # Otherwise, give them a blank copy of the form
    else:
        return render(request, 'bulletin/unsubscribe.html', {'email':useremail})


# Setup view 1
@login_required
def setup1(request):
    user = request.user

    # If they've just completed this stage, then update their time zone
    if request.method == 'POST':
        form = TimezoneForm(request.POST)
        if form.is_valid():
            tz = form.cleaned_data['timezone']
            user = request.user
            user.profile.timezone = tz
            user.profile.save()

        return HttpResponseRedirect(reverse('setup2'))

    # Otherwise, just give them the blank copy of the form

    else:
        # Timezone form
        form = TimezoneForm(initial={'timezone':user.profile.timezone})

    return render(request, 'bulletin/setup_1.html',{'form':form})

# Setup view 2
@login_required
def setup2(request):

    # Get user's current category order

    user = request.user
    usercats = literal_eval(user.profile.catorder)
    totalcats = list(Category.objects.all())

    # Get list of other categories (that user hasn't already selected)

    othercats = [x for x in totalcats if x.category not in usercats]

    # Build list with user's categories in order at the top, followed by remaining choices

    choicelist = []
    for cat in usercats:
        adder = (cat,cat)
        choicelist.append(adder)

    for cat in othercats:
        adder = (cat.category,cat.category)
        choicelist.append(adder)

    if ("Custom alerts","Custom alerts") not in choicelist:
        choicelist.append(("Custom alerts", "Custom alerts"))

    # If form is being submitted...save the new order to the user's profile

    if request.method == 'POST':
        form = SelectForm(choicelist,request.POST)
        if form.is_valid():
            catorder = list(form.cleaned_data['categories'])
            user.profile.catorder = catorder

            # Also need to assign the categories to the user through ForeignKey
            newcats = []
            for cat in catorder:
                try:
                    newcat = Category.objects.get(category=cat)
                    newcats.append(newcat)
                except:
                    continue

            user.profile.categories.set(newcats)
            user.profile.save()

            return HttpResponseRedirect(reverse('setup3'))

    else:
        # Otherwise we give the user an empty form with the curent list for them to order
        form = SelectForm(choicelist,initial={'categories':usercats})

    context = {'form': form, 'loops': int(len(choicelist))}

    return render(request, 'bulletin/setup_2.html', context)

# Setup view 3
@login_required
def setup3(request):

    user = request.user

    # If they're submitting info, process it

    if request.method == 'POST':
        formset = EmailFormset(request.POST)

        if formset.is_valid():
            # Delete all of the user's current email instances (in case they're going back through setup for some reason)
            print("Formset data processed")
            for form in formset:
                print(form.cleaned_data)
            useremails = EmailSend.objects.filter(user=user)
            for i in useremails:
                i.delete()

            # Set some variables for this process
            userformdata = []
            days = dict(zip(calendar.day_name, range(7)));
            strdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
            weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday']

            # Save the form data in a better format for us to use it

            for form in formset:
                # Get each form's data to save to the profile
                formdata = {}
                try:
                    if form.cleaned_data['DELETE']:
                        continue
                    else:
                        day = form.cleaned_data['day']
                        time = form.cleaned_data['time']
                except KeyError:
                    continue

                # Convert whatever they submitted into UTC for the database

                daystr = str(timezone.now().date())
                dtstr = daystr + " " + time
                usertz = pytz.timezone(str(user.profile.timezone))
                naivetime = datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")
                awaretime = usertz.localize(naivetime)

                utctz = pytz.timezone("UTC")

                utctime = awaretime.astimezone(utctz)

                naiveround = naivetime.replace(microsecond=0, second=0, minute=0, hour=0, tzinfo=None)
                utcround = utctime.replace(microsecond=0, second=0, minute=0, hour=0, tzinfo=None)
                delta = utcround - naiveround

                daydiff = delta.days

                # Now create a new email instance for each form item...

                if day in list(days.keys()):
                    adjusted_day = days[day]+daydiff

                    if adjusted_day == 7:
                        adjusted_day = 0

                    formdata['day'] = adjusted_day
                    formdata['time'] = str(utctime.time())

                    newemail = EmailSend(day=adjusted_day,time=str(utctime.time()),user=user)
                    newemail.save()

                # If they picked a multi-day option, we need to make several objects
                elif day == 'Every day':
                    for i in strdays:
                        newemail = EmailSend(day=days[i],time=str(utctime.time()),user=user)
                        newemail.save()

                        formdata['day'] = 'Every day'
                        formdata['time'] = str(utctime.time())

                elif day == 'Weekdays':
                    for i in weekdays:
                        newemail = EmailSend(day=days[i]+daydiff,time=str(utctime.time()),user=user)
                        newemail.save()

                        formdata['day'] = 'Weekdays'
                        formdata['time'] = str(utctime.time())

                userformdata.append(formdata)

            # Add the list with form data to the user profile and save it

            user.profile.emailformdata = userformdata
            user.profile.save()

            return HttpResponseRedirect(reverse('setupcomplete'))

        # Need to add error fixing ??
        else:
            print("Formset data invalid - possibly empty - see POST data below")
            print(request.POST)
            return HttpResponseRedirect(reverse('index'))

    # Otherwise, give them a blank version of the form to fill out
    else:

        initialvals = [{}]

        formset = EmailFormset(initial=initialvals)

        return render(request, 'bulletin/setup_3.html', {'formset':formset})

# Setup complete view
@login_required
def setup_complete(request):

    return render(request, 'bulletin/setup_complete.html')


def csrf_failure(request, reason=""):
    return render(request, '403.html')

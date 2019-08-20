from django.core.management.base import BaseCommand, CommandError

import os
import newspaper

import string

from datetime import datetime, timedelta, timezone

from ast import literal_eval

from decimal import Decimal, ROUND_DOWN

from bulletin.models import Item, Feed, Source, Profile, Category, Story, Topic  
    
from bulletin.news_functions import key_count, key_list_count, word_count, key_compare, count_occurences, topic_count


class Command(BaseCommand):
    
    help = 'Updates news item database'
    
    def handle(self, *args, **options):
    
        counter = 1
        
        filterlist = open(os.path.expanduser('~/Documents/Projects/news/bulletin/filterwords2.txt'), 'r').read().splitlines()

        # Create dictionary of word uses

        wordlistold = open(os.path.expanduser('~/Desktop/news_words.txt'), 'r').read().splitlines()
        valuelist = open(os.path.expanduser('~/Desktop/news_values.txt'), 'r').read().splitlines()

        wordlist = []

        for word in wordlistold:
            wordlist.append(word.lower())

        worddict = {}

        for i in range(1000):
            worddict[wordlist[i]] = float(valuelist[i])

        #Delete old stories

        for thing in Story.objects.all():
            thing.delete()

        #Return lists of feeds to parse and categories to populate with stories

        feeds = Feed.objects.all()

        categories = Category.objects.all()
        
        current_titles = [] 
        
        for item in Item.objects.all():
            current_titles.append(item.title)
        
        #For each category, we need to pull out what the top stories are

        for currcat in categories:
            catfeeds = feeds.filter(category=currcat)
            allpostwords = []
            allkeywords = []

            parsedcatkeys = []

            #Pulling all the items from the feeds in this category


            for feed in catfeeds:
                feed_paper = newspaper.build(feed.link)  #memoize_articles=False to re-download all cached

                catskiplist = literal_eval(currcat.skip_list)
                
                catfilterlist = literal_eval(currcat.filter_words)
                
                for post in feed_paper.articles:

                    try:
                        post.download()
                        post.parse()
                    except:
                        continue
                    
                    if post.title in current_titles:
                        continue
                    else:
                        current_titles.append(post.title)
                    
                    urlvar = False
                    
                    for filtertext in literal_eval(currcat.url_filter):
                        if filtertext in post.url:
                            print(post.title)
                            urlvar = True
                    
                    if urlvar:
                        continue
                    
                    newdesc = post.text[0:500]
                    desc_wc = word_count(newdesc)
                    
                    skipvar = False
                    
                    for phrase in catskiplist:
                        if (phrase in post.title) or (phrase in newdesc):
                            skipvar = True
                    
                    if skipvar:
                        continue
                        

                    # Add try statement to parse time if it is not already parsed
                    try:
                        dt = post.publish_date
                    except:
                        dt = datetime.now(timezone.utc) - timedelta(days=3)

                    # Grabbing keywords from each news item

                    allwords = str(post.title + " " + newdesc)
                    translator = str.maketrans('', '', string.punctuation)
                    allwords = allwords.translate(translator)

                    allwords = allwords.lower()

                    rankings = key_count(allwords)

                    allwords = {k: v for k, v in rankings.items() if v > 0}
                    allkeys = {k: v for k, v in rankings.items() if v > 1}

                    for k in filterlist:
                        allkeys.pop(k, None)
                        allwords.pop(k, None)
                    
                    for k in catfilterlist:
                        allkeys.pop(k, None)
                        allwords.pop(k, None)
                        
                    keyslist = list(allkeys.keys())
                    wordslist = list(allwords.keys())

                    # Populating list of all keywords and post words within the categories
                    allkeywords.append(keyslist)  
                    allpostwords.append(wordslist)
                    
                    
                    # New newspaper logic
#                    post.nlp()   # this might take a long time...
#                    parsedkeys = post.keywords
#
#                    for key in post.keywords:
#                        parsedcatkeys.append(key)


                    if len(wordslist) > 0:   #wordslist
                        #Create Item instance for each news item (to be used later) - leave story null for now
                        newitem = Item(title=post.title, link=post.url, desc=newdesc, desc_wc=desc_wc, date=dt, source=feed.source, newsource=feed.newsource, category=feed.category, keywords=keyslist, top_image=post.top_image, allwords=wordslist)
                        newitem.save()
                    
                        print(f'Item #{counter} created from {newitem.newsource}.')
                        counter += 1

            # Get keywords for all items (but delete anything older than 1 day instead)

            #Convert list of lists of post words into a flat string of all words
            
            print('Calculating which stories to create...')
            
            allitempostwords = ''
            allitemkeywords = []
            
            for item in Item.objects.filter(category=currcat):
                allitemkeywords.append(literal_eval(item.keywords))            
                allitempostwords = allitempostwords + ' ' + item.title
                        
            
#            listcatwords = [item for sublist in allitempostwords for item in sublist]
#            flatcatwords = ' '.join(listcatwords)

            translator = str.maketrans('', '', string.punctuation)
            flatcatwords = allitempostwords.translate(translator)
            flatcatwords = flatcatwords.lower()
#
#            #Count how often words are used for the entire category and compare to reference list
#            catpct = key_compare(flatcatwords,worddict)

            catcount = key_count(flatcatwords)
                    #old || catkeys = {k: v for k, v in catpct.items() if v > 1}
            
            
            #Convert list of lists of keywords into a flat string of all keywords
            listcatkeys = [item for sublist in allitemkeywords for item in sublist]
            flatcatkeys = ' '.join(listcatkeys)
            flatcatkeys = flatcatkeys.lower()

            catkeycount = key_count(flatcatkeys)


            #Create combined keyword rankings dict to populate
            catrank = {}

            #Look up proper factors from category model 

            wordsfactor = float(currcat.words_factor)
            keysfactor = float(currcat.keys_factor)
 
            titlelistset = set(flatcatwords.split(" "))
            keyslistset = set(flatcatkeys.split(" "))
        
            titlecatrank = key_compare(flatcatwords, worddict)
            
            combinedset = keyslistset.intersection(titlelistset)
            
            possiblestories = list(combinedset)
            
            #Populate rankings:
            for key in possiblestories:  #listcatwords
                try:
                    catspecial = catkeycount[key]
                except:
                    catspecial = 0
                try:
                    cattitle = catcount[key]
                except:
                    cattitle = 0
                try: 
                    catrelative = titlecatrank[key]
                except:
                    catrelative = 0 

                catrank[key] = (catspecial * keysfactor) + (cattitle * wordsfactor) + catrelative 
            
            
#            totalparsedkeys = []

#            for item in list(currcat.items.all()):
#                try:
#                    if item.published_24():
#                        keys = literal_eval(item.keywords)
#                        for key in keys:
#                            totalparsedkeys.append(key)
#                        item.elapsed_hours = item.get_elapsed_hours()
#                        item.save()
#                    else:
#                        item.delete()
#                except:
#                     item.delete()


            for item in currcat.items.all():
#                keys = literal_eval(item.keywords)
#                for key in keys:
#                    totalparsedkeys.append(key)
                elapsedhrs = item.get_elapsed_hours()
    
                if elapsedhrs < 24:
                    item.elapsed_hours = item.get_elapsed_hours()
                    item.save()
                else:
                    item.delete()
        
#                if item.elapsed_hours > 35:
#                    item.delete()

#            filteredparsedkeys = [x for x in totalparsedkeys if x not in filterlist]

            # Getting top keywords from ranking methodology above

            topcatkeys = list(sorted(catrank, key=catrank.get, reverse=True)[:15])

            topcatvals = []

            for key in topcatkeys:
                val = catrank[key]
                topcatvals.append(val)

            #Save the top keywords to the category instance
            currcat.topkeys = topcatkeys
            currcat.topkeyvals = topcatvals
            currcat.save()
    
#            parsedcatrank = key_list_count(filteredparsedkeys)
#            topparsedkeys = list(sorted(parsedcatrank, key=parsedcatrank.get, reverse=True)[:10])
#
#            topparsedvals = []
#
#            for key in topparsedkeys:
#                val = parsedcatrank[key]
#                topparsedvals.append(val)


            #Save the top keywords to the category instance
#            currcat.topkeys = topparsedkeys #topcatkeys
#            currcat.topkeyvals = topparsedvals #topcatvals
#            currcat.save()


            #Create Story instance for each of the top keywords in the category --> MUST JOIN ALL KEYWORDS
            for story in topcatkeys:  # in topcatkeys
                newstory = Story(keywords = [story], category = currcat)
                newstory.save()
                print(f'Story created.')
                

            #Now get a list of the Story instances to assign to items
            catstories = currcat.stories.all()
            catstories = [cat for cat in catstories]

            #Combine any keywords that often appear together
            for n, story in zip(range(len(catstories)), catstories):
                stringstory = str(literal_eval(story.keywords)[0])
                
                #Combining stories that have a lot in common
                
                storyitems = Item.objects.filter(category=currcat).filter(keywords__contains=stringstory)
                
                
                for i in range(14):
                    try:     
                        # Count how often the later keywords appear with this one
                        otherstory = catstories[(n+i+1)]
                        otherstring = str(literal_eval(otherstory.keywords)[0])
                        otherstoryhits  = Item.objects.filter(category=currcat).filter(keywords__contains=otherstring)
                        
                        
                        otherstorycount = len(otherstoryhits)
                        combinedstorycount = len(otherstoryhits.filter(keywords__contains=stringstory))

                        # If they are together often enough, make a new story with both keywords...
                        if (combinedstorycount / otherstorycount) > 0.249:
                            newstory = Story(keywords = [stringstory,otherstring], category = currcat)
                            newstory.save()
                                             
                            # ...and prep to delete the old ones
                            story.tracker -= 1
                            story.save()
                            otherstory.tracker -= 1
                            otherstory.save()
                                             
                    except:
                        break
                
                catstories.remove(story)  # remove from list to prevent making duplicate stories 
                
#            for story in currcat.stories.all():
#                if story.tracker > 0:
#                    story.delete()
            
            combinedstories = []
            for story in currcat.stories.all():
                if len(literal_eval(story.keywords)) > 1:
                    combinedstories.append(story)
                
            # *** Find a way to cycle back through the stories and re-append additional keywords ***
            
            for story in combinedstories:
                storykeys = literal_eval(story.keywords)
                
                storyitems = Item.objects.filter(category=currcat).filter(keywords__contains=storykeys[0]).filter(keywords__contains=storykeys[1])
                                
                for word in topcatkeys:
                    if word in storykeys:
                        continue
                    else:
                        worditems = Item.objects.filter(category=currcat).filter(keywords__contains=word)
                        combineditems = storyitems.filter(keywords__contains=word)
                        try:
                            if (len(combineditems) / len(worditems)) > 0.249:
                                newkeylist = storykeys
                                newkeylist.append(word)
                                newstory = Story(keywords=storykeys, category=currcat)
                                newstory.save()

                                story.tracker -=1
                                story.save()

                                wordlist = [word]
                                wordstory = Story.objects.get(category=currcat, keywords=wordlist)
                                wordstory.tracker -=1
                                wordstory.save()
                        except:
                            continue
            
            #Remove identical stories
            
            catstories = currcat.stories.all()
            storysets = []
            for story in catstories:
                storyset = set(literal_eval(story.keywords))
                if storyset in storysets:
                    story.delete()
                    print("Duplicate story deleted.")
                else:
                    storysets.append(storyset)
              
            #Now go through the items and assign them to stories
    
            catitems = currcat.items.all()
            catstories = currcat.stories.all()
            
            #Now go through the items and assign them to stories
            for item in catitems:
                storyscores= {}
                itemset = set(literal_eval(item.keywords))
                titleset = set(item.title.lower().split())
                
                for eachstory in catstories:
                    storyset = set(literal_eval(eachstory.keywords))
                    
                    keycount = len(storyset.intersection(itemset))
                    titlecount = len(storyset.intersection(itemset))
                    
                    storyscores[eachstory] = keycount + (titlecount * 3) - (item.elapsed_hours / 6)

                try:
                    assignedstory = max(storyscores, key=storyscores.get)
                    item.score = storyscores[assignedstory]
                    
                    if storyscores[assignedstory] == -(item.elapsed_hours / 6):
                        item.save()
                    else:
                        item.story = assignedstory
                        item.save()
                        print('Item assigned to story.')
                except:
                    item.score = -99
                    item.save()
                    
                
    
            
            for s in catstories:
                s.numitems = len(Item.objects.filter(category=currcat).filter(story=s))
                s.numkeys = len(literal_eval(s.keywords))
                s.save()
                
            # Getting tagline for all items assigned to a story, in case it's the lead item 
            
            storyitems = currcat.items.filter(story__isnull=False)
            
            for item in storyitems:
                tagline = str(item.desc).partition('.')[0]

                try:
                    keep_running = True
                    counter = 1

                    while keep_running:
                        if (" " in tagline[-4:]) or ("." in tagline[-4:]) or ("-" in tagline[-5:]):
                            tagline = tagline + "." + str(item.desc).split('.')[counter]
                            counter +=1
                        elif len(tagline) < 20:
                            tagline = tagline + "." + str(item.desc).split('.')[counter]
                            counter +=1
                        else:
                            tagline = tagline + '.' + str(item.desc).split(".")[counter][:1]
                            keep_running = False
                except:
                    tagline = item.desc + "..."
                    
                item.slug = tagline
                item.save()
                
        # Once we've created all the items, assign each topic the top few items for it
        
        topiccount = topic_count(Topic.objects.all(),Item.objects.all())
        
        # Penalizing items in stories with a lot of items from the same source
        
        stories = Story.objects.all()
        
        storyitems = Item.objects.filter(story__isnull=False)
        
        for story in stories:
            storyitems = storyitems.filter(story=story).order_by('-score')
            
            for i, item in zip(range(len(storyitems)), storyitems):
                allstories = storyitems[:i]
                print(allstories)
                sourcestories = list((x for x in allstories if x.newsource == item.newsource))
                
                for item in sourcestories:
                    print(item.title + " - " + item.source)
                    
                newscore = Decimal(item.score) - Decimal(10 * len(sourcestories))
                item.score = Decimal(newscore)
                item.save()
            
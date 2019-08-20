# Defining functions to use

from ast import literal_eval

import math

import re

# Definitions for regex sentence splitter

alphabets= "([A-Za-z])"
prefixes = "(Mr|St|Mrs|Ms|Dr|Prof|Capt|Cpt|Lt|Mt|Sen|Rep|Rev|Pres|Gen|Corp|Ala|Ariz|Ark|Calif|Colo|Conn|Del|Fla|Ga|Ill|Ind|Kan|Ky|La|Md|Mass|Mich|Minn|Miss|Mo|Mont|Neb|Nev|Okla|Ore|Pa|Tenn|Vt|Va|Wash|Wis|Wyo)[.]"
suffixes = "(Inc|Ltd|Jr|Sr|Co)"
starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
websites = "[.](com|net|org|io|gov|me|edu|co)"
digits = "([0-9])"

# Use regex to split first sentence out from article text

def split_into_sentences(text):
    text = " " + text + "  "
    # text = text.replace("\n"," ")
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    if "e.g." in text: text = text.replace("e.g.","e<prd>g<prd>")
    if "i.e." in text: text = text.replace("i.e.","i<prd>e<prd>")
    if "D.C." in text: text = text.replace("D.C.","D<prd>C<prd>")
    if "N.H." in text: text = text.replace("N.H.","N<prd>H<prd>")
    if "N.J." in text: text = text.replace("N.J.","N<prd>J<prd>")
    if "N.M." in text: text = text.replace("N.M.","N<prd>M<prd>")
    if "N.Y." in text: text = text.replace("N.Y.","N<prd>Y<prd>")
    if "N.C." in text: text = text.replace("N.C.","N<prd>C<prd>")
    if "N.D." in text: text = text.replace("N.D.","N<prd>D<prd>")
    if "R.I." in text: text = text.replace("R.I.","R<prd>I<prd>")
    if "S.C." in text: text = text.replace("S.C.","S<prd>C<prd>")
    if "S.D." in text: text = text.replace("S.D.","S<prd>D<prd>")
    if "W.Va." in text: text = text.replace("W.Va.","W<prd>Va<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    if "..." in text: text = text.replace("...","<prd><prd><prd>")
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace("\n","<stop>")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences


# Function to count occurrences of each word within an input string

def key_count(inpt):
    counts = dict()
    words = inpt.split()

    for word in words:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return counts

# Function to count occurrences of each word within an input list

def key_list_count(inptlist):
    counts = dict()

    for word in inptlist:
        if word in counts:
            counts[word] += 1
        else:
            counts[word] = 1

    return counts


# Functiont to count number of words in a string

def word_count(inpt):
    tokens = inpt.split()
    n_tokens = len(tokens)
    return n_tokens


# Function to count frequency of words compared to a baseline frequency

def key_compare(inpt,compdict):
    counts = key_count(inpt)
    words = counts.keys()
    base = len(words)

    for word in words:
        newpct = counts[word] / base

        try:
            oldpct = compdict[word]
        except:
            oldpct = newpct

        pctcompare = newpct / oldpct

        counts[word] = math.log(pctcompare)

    return counts


# Function to count frequency of words compared to a baseline frequency

def count_occurrences(s,word):

    count = 0
    for i in range(len(s)):
        if s[i:i+len(word)] == word:
            count += 1
    return count


def regex_count_occurrences(s,word):

    search_pattern = r"(?:^|\b)" + re.escape(word) + r"(?:$|\W)"
    matchlist = re.findall(search_pattern,s)

    return len(matchlist)


# Function to assign items to topics

def topic_count(topiclist,itemlist):

    results = {}


    for i in topiclist:

        itemscores = {}

        # Get items for the topic's categories and the owner's sources

        itemlistfiltered = itemlist.filter(category__in=i.categories.all()).filter(newsource__in=i.user.profile.sources.all())

        for item in itemlistfiltered:

            # For each item, count how many of the topic's keywords it has

            searchtext = (item.title + " " + item.desc)

            #splitsearch = searchtext.split(" ")

            topic_counter = 0

            for topic in literal_eval(i.keywords):

                titlecounter = 0

                titlecounter = regex_count_occurrences(item.title,topic)

                titlecounter = titlecounter * 16

                textcounter = 0

                textcounter = regex_count_occurrences(item.desc,topic)

                textcounter = textcounter * 10

                counter = titlecounter + textcounter

                if counter > 0:
                    print(item.title, " / ", topic, ": ", counter)

#                for word in splitsearch:
#
#                    if word == topic.lower():
#                        counter +=1
#                    else:
#                        counter = counter

                topic_counter += counter

            if topic_counter > 0:
                itemscores[item] = topic_counter


        # Sort items by how many of the topic's words they contain

        topicallitems = list(sorted(itemscores, key=itemscores.get, reverse=True))

        print(topicallitems)

        # Make sure all the top items aren't from the same keyword

        # if len(literal_eval(i.keywords)) > 1:
        #     topicmixeditems = []
        #     topicunmixeditems = []
        #     topickeywords = []

        #     for item in topicallitems:
        #         newwords = 0
        #         searchtext = (item.title + " " + item.desc)
        #         for topic in literal_eval(i.keywords):
        #             counter = count_occurrences(searchtext,topic)
        #             if counter > 0 and topic not in topickeywords:
        #                 topickeywords.append(topic)
        #                 newwords += 1
        #         if newwords > 0:
        #             topicmixeditems.append(item)
        #         else:
        #             topicunmixeditems.append(item)

        # Make sure all the top items aren't from the same story
        topictopitems = []
        topicstories = []

        for item in topicallitems:
            if len(topictopitems)>3:  #2
                break

            if item.story in topicstories:
                continue
            else:
                topictopitems.append(item)
                topicstories.append(item.story)

        if len(topictopitems)<4:  #3
            for item in topicallitems:
                if len(topictopitems)>3:  #2
                    break

                if item in topictopitems:
                    continue
                else:
                    topictopitems.append(item)


        results[i.title] = topictopitems
        i.items.set(topictopitems)
        i.numitems = len(topicallitems)
        i.save()

    return results


# Determine average score of a list of items

def avg_score(itemlist):

        itemscores = 0

        for item in itemlist:
            itemscores += item.score

        return itemscores/len(itemlist)

def suffix(d):
    return 'th' if 11<=d<=13 else {1:'st',2:'nd',3:'rd'}.get(d%10, 'th')

def custom_strftime(format, t):
    return t.strftime(format).replace('{S}', str(t.day) + suffix(t.day))

def google_lat_lng(apiKey, city):
    """
    Returns the latitude and longitude of a location using the Google Maps Geocoding API.
    API: https://developers.google.com/maps/documentation/geocoding/start

    # INPUT -------------------------------------------------------------------
    apiKey                  [str]
    address                 [str]

    # RETURN ------------------------------------------------------------------
    lat                     [float]
    lng                     [float]
    """
    import requests
    url = ('https://maps.googleapis.com/maps/api/geocode/json?address={}&key={}'.format(city.replace(' ','+'), apiKey))
    try:
        response = requests.get(url)
        resp_json_payload = response.json()
        lat = resp_json_payload['results'][0]['geometry']['location']['lat']
        lng = resp_json_payload['results'][0]['geometry']['location']['lng']
    except:
        print('ERROR: {}'.format(city))
        lat = 0
        lng = 0
    return lat, lng





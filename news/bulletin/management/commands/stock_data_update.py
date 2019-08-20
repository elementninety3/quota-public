from django.core.management.base import BaseCommand, CommandError

import os
from iexfinance.refdata import get_symbols


class Command(BaseCommand):

    help = 'Creates user stories for all users and stories'

    def handle(self, *args, **options):

        stockdata = get_symbols(token="pk_8f5b78cb3a204a41919d2ce5b3ebdfd2")

        stockfile = open(os.path.expanduser('~/bulletyn/news/bulletin/stocklist.txt'),'w')

        tickerfile = open(os.path.expanduser('~/bulletyn/news/bulletin/tickerlist.txt'),'w')

        newlist = []
        tickerlist = []

        for listing in stockdata:
            limit = 37 - len(listing['symbol'])
            shortname = listing['name'][:limit].rstrip()
            title = shortname + " (" + listing['symbol'] + ")"
            newlist.append(title)
            tickerlist.append(listing['symbol'])

        for s in newlist:
            stockfile.write('%s\n' % s)

        stockfile.close()

        print("Stock name file updated")

        for s in tickerlist:
            tickerfile.write('%s\n' % s)

        tickerfile.close()

        print("Ticker symbol file updated")

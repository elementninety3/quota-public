from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

import pytz

class TimezoneMiddleware(object):

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # make sure they are authenticated so we know we have their tz info.
        if request.user.is_authenticated:
            # we are getting the users timezone that in this case is stored in 
            # a user's profile
            try:
                tz_str = request.user.profile.timezone
                timezone.activate(pytz.timezone(tz_str))
            except:
                timezone.activate(pytz.timezone("US/Eastern"))
        # otherwise deactivate and the default time zone will be used anyway
        else:
            timezone.deactivate()

        response = self.get_response(request)
        return response
    
#    def process_request(self, request):
#        timezone.activate(pytz.timezone('US/Pacific'))
from django.core.management.base import BaseCommand, CommandError


from django.contrib.auth.models import User
from bulletin.models import Story, UserStory



class Command(BaseCommand):
    
    help = 'Creates user stories for all users and stories'
    
    def handle(self, *args, **options):
        
        for createuser in User.objects.filter(is_active=True):
            for createstory in Story.objects.all():
                userstory = UserStory(user=createuser, story=createstory)
                userstory.save()
        
        
        
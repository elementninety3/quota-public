from django.core.management.base import BaseCommand, CommandError


from bulletin.models import Item
    

class Command(BaseCommand):
    
    help = 'Deletes all itmes - for development use only'
    
    def handle(self, *args, **options):
        
        for item in Item.objects.all():
            item.delete()
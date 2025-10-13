# Seeding carries no marks but may help you test your work.
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Insert sample data into database for user testing'

    def handle(self, *args, **options):
        print('No seeding command provided')

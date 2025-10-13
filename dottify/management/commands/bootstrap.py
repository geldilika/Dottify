# You may not need this file, depending on how your project is configured.
# This will be called before we run our API and view tests, in case you need
# to set up the database beforehand.
from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = 'Initial boostrapper for Dottify deployments'

    def handle(self, *args, **options):
        print('No setup or configuration provided for first-time deplyoment')

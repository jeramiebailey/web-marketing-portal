from django.core.management.base import BaseCommand, CommandError
from account_health.models import AccountHealth
from organizations.models import Organization
from account_health.tasks import pull_account_health_analytics, pull_all_account_data

class Command(BaseCommand):
    help = 'Creates Account Health objects for each organization and begins data setup'

    def handle(self, *args, **kwargs):
        missing_account_health_organizations = Organization.objects.filter(account_health__isnull=True)

        if missing_account_health_organizations and missing_account_health_organizations[0]:
            for organization in missing_account_health_organizations:
                created_account_health_object = AccountHealth.objects.create(account=organization)

            self.stdout.write(self.style.SUCCESS(f'Successfully created {missing_account_health_organizations.count()} objects'))

        else:
            self.stdout.write(self.style.ERROR(f'There are no missing account health objects'))
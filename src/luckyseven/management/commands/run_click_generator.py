"""
Management command to manually run click generator for a specific affiliate.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from luckyseven.models import Affiliate, Job
from luckyseven.tasks import click_generator
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Manually run click generator for a specific affiliate ID'

    def add_arguments(self, parser):
        parser.add_argument(
            'affiliate_id',
            type=str,
            help='The affiliate ID to run click generator for'
        )
        parser.add_argument(
            '--async',
            action='store_true',
            help='Run the task asynchronously using Celery'
        )

    def handle(self, *args, **options):
        affiliate_id = options['affiliate_id']
        run_async = options['async']

        # Validate affiliate exists
        try:
            affiliate = Affiliate.objects.get(affiliate_id=affiliate_id)
            self.stdout.write(
                self.style.SUCCESS(f'Found affiliate: {affiliate.affiliate_id} ({affiliate.affiliate_encoded_value})')
            )
        except Affiliate.DoesNotExist:
            raise CommandError(f"Affiliate with ID '{affiliate_id}' not found")

        if run_async:
            # Run asynchronously using Celery
            self.stdout.write(
                self.style.WARNING(f'Starting click generator task for affiliate {affiliate_id} asynchronously...')
            )
            task = click_generator.delay(affiliate_id)
            self.stdout.write(
                self.style.SUCCESS(f'Task started with ID: {task.id}')
            )
        else:
            # Run synchronously
            self.stdout.write(
                self.style.WARNING(f'Running click generator for affiliate {affiliate_id} synchronously...')
            )
            try:
                click_generator(affiliate_id)
                self.stdout.write(
                    self.style.SUCCESS('Click generator completed successfully')
                )
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Click generator failed: {str(e)}')
                )
                raise CommandError(f'Click generator failed: {str(e)}')

from django.core.management.base import BaseCommand
from startlet.models import Branch
from startlet.utils import generate_slots_for_branch


class Command(BaseCommand):
    help = "Generate the rolling 7-day time slot window for every branch. Safe to run daily (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--days-ahead', type=int, default=7)

    def handle(self, *args, **options):
        days_ahead = options['days_ahead']
        for branch in Branch.objects.all():
            count = generate_slots_for_branch(branch, days_ahead=days_ahead)
            self.stdout.write(f"{branch.name}: {count} slots created for next {days_ahead} days")

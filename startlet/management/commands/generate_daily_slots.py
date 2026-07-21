from django.core.management.base import BaseCommand
from startlet.models import Branch, SlotGenerationLog
from startlet.utils import generate_slots_for_branch


class Command(BaseCommand):
    help = "Generate the rolling 7-day time slot window for every branch. Safe to run daily (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument('--days-ahead', type=int, default=7)

    def handle(self, *args, **options):
        days_ahead = options['days_ahead']
        branches = Branch.objects.all()
        lines = []
        total_slots = 0
        success = True

        for branch in branches:
            try:
                count = generate_slots_for_branch(branch, days_ahead=days_ahead)
                total_slots += count
                line = f"{branch.name}: {count} slots created for next {days_ahead} days"
            except Exception as e:
                success = False
                line = f"{branch.name}: FAILED - {e}"
            self.stdout.write(line)
            lines.append(line)

        SlotGenerationLog.objects.create(
            success=success,
            branches_processed=branches.count(),
            slots_created=total_slots,
            details="\n".join(lines),
        )

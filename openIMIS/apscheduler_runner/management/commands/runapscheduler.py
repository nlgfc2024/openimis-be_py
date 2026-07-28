import importlib
import importlib.util
from copy import deepcopy

from apscheduler.schedulers.blocking import BlockingScheduler
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Run openIMIS scheduled tasks in a dedicated process"

    def handle(self, *args, **options):
        scheduler = BlockingScheduler(deepcopy(settings.SCHEDULER_CONFIG))

        for app_name in settings.OPENIMIS_APPS:
            scheduled_tasks_name = f"{app_name}.scheduled_tasks"

            if importlib.util.find_spec(scheduled_tasks_name) is None:
                continue

            scheduled_tasks = importlib.import_module(scheduled_tasks_name)
            scheduled_tasks.schedule_tasks(scheduler)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Registered scheduled tasks from {app_name}"
                )
            )

        self.stdout.write(
            self.style.SUCCESS("Starting dedicated APScheduler process")
        )

        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            self.stdout.write("Scheduler stopped")

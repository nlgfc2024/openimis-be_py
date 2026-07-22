import os
import sys
# This scheduler config will:
# - Store jobs in the project database
# - Execute jobs in threads inside the application process, for production use, we could use a dedicated process
SCHEDULER_CONFIG = {
    "apscheduler.jobstores.default": {
        "class": "django_apscheduler.jobstores:DjangoJobStore"
    },
    "apscheduler.executors.processpool": {"type": "threadpool"},
}

def _env_bool(name, default=False):
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


def _is_gunicorn_process():
    return any("gunicorn" in os.path.basename(arg) for arg in sys.argv)


# Production schedulers must run in a single dedicated process, normally:
#   python manage.py runapscheduler
#
# Do not start a BackgroundScheduler inside gunicorn workers. With multiple
# replicas/workers, each process would register and run the same jobs.
SCHEDULER_AUTOSTART = _env_bool("SCHEDULER_AUTOSTART") and not _is_gunicorn_process()

# Normally, one creates a "scheduler" method that calls the appropriate scheduler.add_job but since we are in a
# modular architecture and calling only once from the core module, this has to be dynamic.
# This list will be called with scheduler.add_job() as specified:
# Note that the document implies that the time is local and follows DST but that seems false and in UTC regardless
SCHEDULER_JOBS = [
    # {
    #     "method": "policy_notification.tasks.send_notification_messages",
    #     "args": ["cron"],
    #     "kwargs": {"id": "openimis_notification_batch", 'day_of_week': '*',
    #                "hour": "8,12,16,20", "replace_existing": True},
    # },
    # {
    #     "method": "claim_ai_quality.tasks.claim_ai_processing",
    #     "args": ["cron"],
    #     "kwargs": {"id": "claim_ai_processing",
    #                "hour": 0
    #                "minute", 30
    #                "replace_existing": True},
    # },
]
# This one is called directly with the scheduler object as first parameter. The methods can schedule things on their own
SCHEDULER_CUSTOM = [
    {
        "method": "core.tasks.sample_method",
        "args": ["sample"],
        "kwargs": {"sample_named": "param"},
    },
]

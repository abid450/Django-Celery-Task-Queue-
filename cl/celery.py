import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cl.settings')

# Create Celery application
app = Celery('cl')

# Configure Celery using settings from Django settings.py
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load tasks from all registered Django apps
app.autodiscover_tasks()

# Debug task to test Celery is working
@app.task(bind=True)
def debug_task(self):
    """
    Debug task to verify Celery is running
    Usage: debug_task.delay()
    """
    print(f'Request: {self.request!r}')
    return f'Task executed successfully with ID: {self.request.id}'


# ============= Periodic Tasks Schedule (Celery Beat) =============
# These tasks will run automatically at scheduled intervals

app.conf.beat_schedule = {
    # Clean up expired verifications daily at midnight
    'cleanup-expired-verifications': {
        'task': 'accounts.tasks.cleanup_expired_verifications',
        'schedule': crontab(hour=0, minute=0),  # Daily at 00:00
        'options': {
            'expires': 3600,  # Task expires after 1 hour if not picked up
        }
    },
    
    # Send daily report every day at 9 AM
    'send-daily-report': {
        'task': 'accounts.tasks.send_daily_report',
        'schedule': crontab(hour=9, minute=0),  # Daily at 09:00
        'options': {
            'expires': 1800,  # 30 minutes
        }
    },
    
    # Check and process pending emails every 5 minutes
    'process-pending-emails': {
        'task': 'accounts.tasks.process_pending_emails',
        'schedule': crontab(minute='*/5'),  # Every 5 minutes
        'options': {
            'expires': 300,  # 5 minutes
        }
    },
    
    # Clean up old logs weekly on Sunday at 2 AM
    'cleanup-old-logs': {
        'task': 'accounts.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0, day_of_week=0),  # Sunday 2 AM
        'options': {
            'expires': 7200,  # 2 hours
        }
    },
}

# Optional: Configure task routes (which queue to use for which task)
app.conf.task_routes = {
    'accounts.tasks.send_verification_email': {'queue': 'email'},
    'accounts.tasks.send_welcome_email': {'queue': 'email'},
    'accounts.tasks.cleanup_expired_verifications': {'queue': 'cleanup'},
    'accounts.tasks.send_daily_report': {'queue': 'report'},
}

# Optional: Configure task time limits
app.conf.task_time_limit = 30 * 60  # 30 minutes
app.conf.task_soft_time_limit = 20 * 60  # 20 minutes

# Optional: Configure task result expiry
app.conf.result_expires = 86400  # 1 day

# Optional: Configure task tracking (store task results)
app.conf.task_track_started = True
app.conf.task_send_sent_event = True

# Optional: Configure worker preferences
app.conf.worker_prefetch_multiplier = 4
app.conf.worker_max_tasks_per_child = 100
app.conf.worker_max_memory_per_child = 200000  # 200MB


# ============= Custom Task Classes (Optional) =============

class BaseTaskWithRetry(app.Task):
    """
    Base task class with automatic retry functionality
    """
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600
    retry_jitter = True


# Apply custom task class to specific tasks
app.register_task(BaseTaskWithRetry())


# ============= Utility Functions =============

def get_celery_status():
    """
    Check Celery connection status
    Returns: dict with status information
    """
    try:
        # Try to ping Celery
        inspect = app.control.inspect()
        stats = inspect.stats()
        active = inspect.active()
        
        if stats:
            return {
                'status': 'connected',
                'workers': len(stats),
                'stats': stats,
                'active_tasks': active
            }
        else:
            return {
                'status': 'no_workers',
                'message': 'Celery is running but no workers are connected'
            }
    except Exception as e:
        return {
            'status': 'disconnected',
            'error': str(e),
            'message': 'Cannot connect to Celery broker. Make sure Redis is running.'
        }


# Optional: Print Celery configuration when module loads (for debugging)
if __name__ == '__main__':
    print("Celery app configured for 'cl' project")
    print(f"Broker URL: {app.conf.broker_url}")
    print(f"Result backend: {app.conf.result_backend}")
    print(f"Beat schedule: {app.conf.beat_schedule.keys()}")
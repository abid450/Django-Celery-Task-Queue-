# config/__init__.py
from cl.celery import app as celery_app

__all__ = ('celery_app',)
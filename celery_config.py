# Celery Configuration for Financial Document Analyzer
# This module configures Celery for background task processing

from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# Redis configuration
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "financial_analyzer",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["worker_tasks"]  # Include task modules
)

# Celery configuration
celery_app.conf.update(
    # Task serialization
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    
    # Task routing
    task_routes={
        "worker_tasks.analyze_document": {"queue": "document_analysis"},
        "worker_tasks.cleanup_old_results": {"queue": "maintenance"},
    },
    
    # Task execution
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    
    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    
    # Worker settings
    worker_max_tasks_per_child=50,
    worker_disable_rate_limits=False,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-old-results": {
            "task": "worker_tasks.cleanup_old_results",
            "schedule": 3600.0,  # Run every hour
        },
    },
)

# Task priority settings
celery_app.conf.task_default_priority = 5
celery_app.conf.worker_enable_priority_delivery = True
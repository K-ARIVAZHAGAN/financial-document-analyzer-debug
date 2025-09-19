#!/usr/bin/env python3
"""
Celery Worker Startup Script for Financial Document Analyzer
Run this script to start the background worker processes
"""

import os
import sys
from celery import Celery

# Add current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from celery_config import celery_app

if __name__ == "__main__":
    # Start Celery worker
    celery_app.worker_main([
        'worker',
        '--loglevel=info',
        '--concurrency=2',  # Number of concurrent workers
        '--queues=document_analysis,maintenance',
        '--hostname=worker@%h'
    ])
"""
Job utilities to prevent duplicate task execution.
"""
from django.utils import timezone
from datetime import timedelta
from .models import Job


def should_skip_job(task_name, time_window_seconds=20):
    """
    Check if a job with the same task_name was created within the specified time window.
    If yes, skip creating a new job to prevent duplicates.
    
    Args:
        task_name (str): The name of the task to check
        time_window_seconds (int): Time window in seconds to check for duplicates (default: 20)
        
    Returns:
        bool: True if job should be skipped (duplicate found), False if job should proceed
    """
    # Calculate the time threshold
    time_threshold = timezone.now() - timedelta(seconds=time_window_seconds)
    
    # Check if a job with the same task_name was created within the time window
    recent_job = Job.objects.filter(
        task_name=task_name,
        started_at__gte=time_threshold
    ).first()
    
    if recent_job:
        # Duplicate found - skip this job
        return True
    
    # No duplicate found - proceed with job
    return False


def create_job_if_not_duplicate(task_name, time_window_seconds=20):
    """
    Create a job only if no duplicate exists within the time window.
    
    Args:
        task_name (str): The name of the task
        time_window_seconds (int): Time window in seconds to check for duplicates (default: 20)
        
    Returns:
        Job or None: The created job if no duplicate found, None if duplicate found
    """
    if should_skip_job(task_name, time_window_seconds):
        # Duplicate found - skip creating job
        return None
    
    # No duplicate found - create the job
    job = Job.objects.create(
        task_name=task_name,
        status='running'
    )
    return job

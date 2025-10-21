"""
Celery tasks for luckyseven project.
"""

from celery import shared_task
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from .models import Click, Affiliate, Job
from .click_generator_utils import process_affiliate_click_generation, fetch_clicks_from_everflow, clean_clicks, process_clicks, create_clicks
from .click_processor_utils import process_ready_clicks
from .conversion_processor_utils import process_ready_conversions
from .jobs_utils import should_skip_job
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task(name='click_generator')
def click_generator(affiliate_id):
    """
    Generate clicks for a specific affiliate.
    Scheduled at various times throughout the hour.
    """
    task_name = f"click_generator_{affiliate_id}"
    job = Job.objects.create(
        task_name=task_name,
        status='running'
    )
    
    # Initialize variables
    affiliate = None
    daily_revenue_goal = None
    daily_revenue_runtime = None
    average_cost_per_conversion = None
    daily_conversions_needed = None
    conversion_ratio_runtime = None
    daily_clicks_needed = None
    
    try:
        # Process affiliate click generation using utils
        result = process_affiliate_click_generation(affiliate_id)
        affiliate = result['affiliate']
        daily_revenue_goal = result['daily_revenue_goal']
        daily_revenue_runtime = result['daily_revenue_runtime']
        average_cost_per_conversion = result['average_cost_per_conversion']
        daily_conversions_needed = result['daily_conversions_needed']
        conversion_ratio_runtime = result['conversion_ratio_runtime']
        daily_clicks_needed = result['daily_clicks_needed']
        
        # Fetch clicks from Everflow for the last 13 days
        now = timezone.now()
        from_datetime = (now - timedelta(days=13)).strftime("%Y-%m-%d %H:%M:%S")
        to_datetime = (now + timedelta(minutes=10) - timedelta(days=13)).strftime("%Y-%m-%d %H:%M:%S")
        
        clicks = fetch_clicks_from_everflow(from_datetime, to_datetime, affiliate.geos)
        
        filtered_clicks = clean_clicks(clicks)
        
        logger.info(f"Affiliate {affiliate_id} - Revenue goal: {daily_revenue_goal}, Runtime revenue: {daily_revenue_runtime}, Avg cost per conversion: {average_cost_per_conversion}, Daily conversions needed: {daily_conversions_needed}, Conversion ratio runtime: {conversion_ratio_runtime}%, Daily clicks needed: {daily_clicks_needed}")
        logger.info(f"Fetched {len(clicks)} clicks from Everflow for affiliate {affiliate_id}")
        logger.info(f"Filtered {len(filtered_clicks)} clicks after cleaning for affiliate {affiliate_id}")
        
        # Debug: Check if filtered_clicks is accessible
        logger.info(f"DEBUG: filtered_clicks length = {len(filtered_clicks)}")
        
        # Debug: Check if we have enough filtered clicks to achieve our goals
        # Since we run every hour, multiply filtered_clicks by 24 to get daily projection
        daily_projected_clicks = len(filtered_clicks) * 24
        if daily_projected_clicks >= daily_clicks_needed:
            logger.info(f"✅ GOAL ACHIEVED: We have {len(filtered_clicks)} quality clicks/hour, projected {daily_projected_clicks} daily, need {daily_clicks_needed} clicks")
        else:
            logger.info(f"❌ GOAL NOT MET: We have {len(filtered_clicks)} quality clicks/hour, projected {daily_projected_clicks} daily, need {daily_clicks_needed} clicks (shortage: {daily_clicks_needed - daily_projected_clicks})")
        
        # Process the filtered clicks
        processed_clicks = process_clicks(filtered_clicks, daily_clicks_needed, affiliate, conversion_ratio_runtime)
        
        # Create Click objects in the database
        created_count, skipped_count = create_clicks(processed_clicks)
        
        # Task logic will go here
        pass
    except ObjectDoesNotExist:
        job.status = 'failed'
        job.error_message = f"Affiliate with ID '{affiliate_id}' not found"
        job.completed_at = timezone.now()
        job.save()
        logger.error(f"Affiliate with ID '{affiliate_id}' not found")
        return
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        raise
    else:
        job.status = 'completed'
        # Debug: Check if variables are accessible in else block
        logger.info(f"DEBUG: In else block - clicks length: {len(clicks)}, filtered_clicks length: {len(filtered_clicks)}")
        job.completed_message = f"Click generation completed for affiliate {affiliate_id}. Payout target: {affiliate.payout_target}, Daily revenue goal: {daily_revenue_goal}, Runtime revenue: {daily_revenue_runtime}, Avg cost per conversion: {average_cost_per_conversion}, Daily conversions needed: {daily_conversions_needed}, Conversion ratio runtime: {conversion_ratio_runtime}%, Daily clicks needed: {daily_clicks_needed}, Clicks found from Everflow: {len(clicks)}, Filtered clicks: {len(filtered_clicks)}, Processed clicks: {len(processed_clicks)}, Created in DB: {created_count}, Skipped duplicates: {skipped_count}"
        job.completed_at = timezone.now()
        job.save()


@shared_task(name='click_processor')
def click_processor():
    """
    Process pending clicks.
    Runs every minute.
    """
    task_name = "click_processor"
    
    # Check for duplicates within 20 seconds
    if should_skip_job(task_name, 20):
        return  # Skip duplicate job
    
    job = Job.objects.create(
        task_name=task_name,
        status='running'
    )
    
    try:
        # Process ready clicks
        processed_count = process_ready_clicks()
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        raise
    else:
        job.status = 'completed'
        job.completed_message = f'Click processing completed. Processed {processed_count} clicks'
        job.completed_at = timezone.now()
        job.save()


@shared_task(name='conversion_processor')
def conversion_processor():
    """
    Process conversions for processed clicks.
    Runs every minute.
    """
    task_name = "conversion_processor"
    
    # Check for duplicates within 20 seconds
    if should_skip_job(task_name, 20):
        return  # Skip duplicate job
    
    job = Job.objects.create(
        task_name=task_name,
        status='running'
    )
    
    try:
        # Process ready conversions
        converted_count = process_ready_conversions()
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        raise
    else:
        job.status = 'completed'
        job.completed_message = f'Conversion processing completed. Processed {converted_count} conversions'
        job.completed_at = timezone.now()
        job.save()


@shared_task(name='r1_processor')
def r1_processor():
    """
    Process R1 performance data.
    Runs daily at 6:00 AM.
    """
    task_name = "r1_processor"
    job = Job.objects.create(
        task_name=task_name,
        status='running'
    )
    
    try:
        # Task logic will go here
        pass
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        raise
    else:
        job.status = 'completed'
        job.completed_message = 'R1 processing completed'
        job.completed_at = timezone.now()
        job.save()


@shared_task(name='r7_processor')
def r7_processor():
    """
    Process R7 performance data.
    Runs daily at 7:00 AM.
    """
    task_name = "r7_processor"
    job = Job.objects.create(
        task_name=task_name,
        status='running'
    )
    
    try:
        # Task logic will go here
        pass
    except Exception as e:
        job.status = 'failed'
        job.error_message = str(e)
        job.completed_at = timezone.now()
        job.save()
        raise
    else:
        job.status = 'completed'
        job.completed_message = 'R7 processing completed'
        job.completed_at = timezone.now()
        job.save()

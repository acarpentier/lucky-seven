"""
R1 processor utilities for luckyseven project.
"""

from datetime import timedelta, datetime, timezone
from django.utils import timezone as django_timezone
import random
import requests
from .models import Click


def fetch_r1():
    """
    Fetch all clicks that have converted between the full 2 days ago time range.
    
    Returns:
        list: List of converted clicks from 2 days ago
    """
    now = django_timezone.now()
    day_before_yesterday_start = (now - timedelta(days=2)).replace(hour=0, minute=0, second=0, microsecond=0)
    day_before_yesterday_end = (now - timedelta(days=2)).replace(hour=23, minute=59, second=59, microsecond=999999)
    
    # Fetch all clicks that converted between the time range
    converted_clicks = Click.objects.filter(
        is_converted=True,
        is_converted_datetime__gte=day_before_yesterday_start,
        is_converted_datetime__lte=day_before_yesterday_end
    ).order_by('is_converted_datetime')
    
    return list(converted_clicks)


def filter_r1(conversions):
    """
    Filter R1 conversions data.
    Splits conversions into two lists: one to flag for R1 and one to delete.
    
    Args:
        conversions: List of converted clicks from 2 days ago
        
    Returns:
        dict: Processing results with flagged and deleted lists
    """
    if not conversions:
        return {
            'flagged_conversions': [],
            'deleted_conversions': [],
            'total_processed': 0
        }
    
    # Select random percentage between 45% and 55% for R1 flagging
    selection_percentage = random.uniform(0.45, 0.55)
    num_to_select = int(len(conversions) * selection_percentage)
    selected_conversions = random.sample(conversions, num_to_select)
    
    # Split into flagged (for R1) and deleted lists
    flagged_conversions = selected_conversions
    deleted_conversions = [conv for conv in conversions if conv not in selected_conversions]
    
    return {
        'flagged_conversions': flagged_conversions,
        'deleted_conversions': deleted_conversions,
        'total_processed': len(conversions)
    }


def delete_conversions(conversions_to_delete):
    """
    Delete all clicks that are present in the deleted_conversions list.
    
    Args:
        conversions_to_delete: List of Click objects to delete
        
    Returns:
        int: Number of conversions deleted
    """
    if not conversions_to_delete:
        return 0
    
    # Extract IDs for bulk deletion
    conversion_ids = [conv.id for conv in conversions_to_delete]
    
    # Delete all conversions in bulk
    deleted_count, _ = Click.objects.filter(id__in=conversion_ids).delete()
    
    return deleted_count


def process_conversions(conversions):
    """
    Process conversions for R1 by making callbacks for each conversion.
    
    Args:
        conversions: List of Click objects to process
        
    Returns:
        dict: Processing results with success and failure counts
    """
    success_count = 0
    failure_count = 0
    
    for conversion in conversions:
        transaction_id = conversion.transaction_id
        
        # Get current UTC timestamp
        utc_timestamp = int(datetime.now(timezone.utc).timestamp())
        
        # Get current EDT datetime for Redis storage
        edt_datetime = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')
        
        # Construct the callback URL
        callback_url = f"https://www.algyle.com/?nid=115&transaction_id={transaction_id}&timestamp={utc_timestamp}&adv_event_id=58"
        
        print(f"🔗 Making callback for transaction {transaction_id}: {callback_url}")
        
        try:
            # Make the GET request
            response = requests.get(callback_url, timeout=30)
            
            if response.status_code in [200, 204]:
                success_count += 1
                print(f"✅ Success for transaction {transaction_id}")
            else:
                failure_count += 1
                print(f"❌ Failed for transaction {transaction_id} - Status: {response.status_code}")
                
        except Exception as e:
            failure_count += 1
            print(f"❌ Exception for transaction {transaction_id}: {str(e)}")
        
        # Update click with r1_datetime regardless of success/failure
        conversion.r1_datetime = django_timezone.now()
        conversion.save()
    
    return {
        'processed_count': len(conversions),
        'success_count': success_count,
        'failure_count': failure_count
    }

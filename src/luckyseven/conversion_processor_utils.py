"""
Utility functions for conversion processor tasks.
"""

from django.utils import timezone
from .models import Click
import logging
import requests
from datetime import datetime
import time
import random

logger = logging.getLogger(__name__)


def post_conversion(click: Click) -> str:
    """
    Post a conversion to the conversion URL and return conversion_id.
    
    Args:
        click: Click object to convert
        
    Returns:
        str: Conversion ID from the response headers
    """
    try:
        now_edt = datetime.now()
        now_utc = datetime.now(timezone.utc)
        timestamp = int(now_utc.timestamp())
        transaction_id = click.transaction_id or ''
        
        logger.info(f"🕐 CONVERSION TIMEZONE: EDT '{now_edt}' -> UTC '{now_utc}' -> timestamp {timestamp}")
        
        conversion_url = f"https://www.biphic.com/?transaction_id={transaction_id}&user_id={transaction_id}&asub1=s2s&timestamp={timestamp}"
        
        # Make the GET request
        response = requests.get(conversion_url, timeout=30)
        response.raise_for_status()
        
        # Extract conversion_id from headers
        conversion_id = response.headers.get('x-conversion-id', '')
        
        logger.info(f"Posted conversion for click {click.id}, conversion_id: {conversion_id}")
        return conversion_id
        
    except Exception as e:
        logger.error(f"Error posting conversion for click {click.id}: {str(e)}")
        return ''


def process_ready_conversions() -> int:
    """
    Process clicks that are ready for conversion.
    
    Returns:
        int: Number of conversions successfully processed
    """
    # Get clicks that are ready for conversion and have been processed
    ready_conversions = Click.objects.filter(
        to_convert=True,
        to_convert_datetime__lte=timezone.now(),
        is_processed=True,
        is_converted=False
    )
    
    converted_count = 0
    total_conversions = len(ready_conversions)
    
    # Calculate sleep interval: 10 seconds / number of conversions to process
    # This spreads processing over the 10-second window
    if total_conversions > 0:
        sleep_interval = 10.0 / total_conversions
        logger.info(f"Processing {total_conversions} conversions with {sleep_interval:.2f}s interval between conversions")
    
    for i, click in enumerate(ready_conversions):
        try:
            logger.info(f"Processing conversion for click {click.id} for affiliate {click.affiliate_id}")
            
            # Post conversion and get conversion_id
            conversion_id = post_conversion(click)
            
            # Save conversion_id and mark as converted
            click.conversion_id = conversion_id
            click.is_converted = True
            click.is_converted_datetime = timezone.now()
            click.save()
            
            converted_count += 1
            
            # Sleep between conversions to spread processing over the minute
            if i < total_conversions - 1:  # Don't sleep after the last conversion
                sleep_time = sleep_interval + random.uniform(-0.1, 0.1)  # Add small random variation
                time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error processing conversion for click {click.id}: {str(e)}")
            continue
    
    logger.info(f"Successfully processed {converted_count} conversions")
    return converted_count

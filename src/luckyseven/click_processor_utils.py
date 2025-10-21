"""
Utility functions for click processor tasks.
"""

from django.utils import timezone
from .models import Click
import logging
import requests
from datetime import datetime
import os
import time
import random

logger = logging.getLogger(__name__)


def post_click(click: Click) -> str:
    """
    Post a click to the affiliate URL and return transaction_id.
    
    Args:
        click: Click object to process
        
    Returns:
        str: Transaction ID from the response
    """
    try:
        # Build URL: https://www.goplay4.com/{affiliate_encoded_value}/KM15N5P/
        base_url = f"https://www.goplay4.com/{click.affiliate_encoded_value}/KM15N5P/"
        
        # Convert to_process_datetime to Unix timestamp for Everflow
        # Handle both datetime objects and string formats
        process_datetime = click.to_process_datetime
        if isinstance(process_datetime, str):
            process_datetime_edt = datetime.strptime(process_datetime, "%Y-%m-%d %H:%M:%S")
        else:
            process_datetime_edt = process_datetime
        
        process_datetime_utc = process_datetime_edt.astimezone(timezone.utc)
        unix_timestamp = int(process_datetime_utc.timestamp())
        
        params = {
            'async': 'json',
            'sub1': click.sub1,
            'sub2': click.sub2,
            'user_ip': click.ip_address,
            'user_agent': click.user_agent,
            'referer': '',  # Keep referer empty
            'language': click.language,
            'timestamp': unix_timestamp
        }
        
        headers = {
            'User-Agent': click.user_agent,
            'Accept-Language': click.language
        }
        
        # Make the request
        response = requests.get(base_url, params=params, headers=headers, timeout=30)
        
        # Extract transaction_id from response
        transaction_id = ''
        try:
            click_result = response.json()
            transaction_id = click_result.get('transaction_id', '')
        except:
            pass
            
        logger.info(f"Posted click {click.id} to affiliate {click.affiliate_id}, transaction_id: {transaction_id}")
        return transaction_id
        
    except Exception as e:
        logger.error(f"Error posting click {click.id}: {str(e)}")
        return ''


def process_ready_clicks() -> int:
    """
    Process clicks that are ready for processing.
    
    Returns:
        int: Number of clicks successfully processed
    """
    # Get clicks that are ready for processing
    ready_clicks = Click.objects.filter(
        to_process=True,
        to_process_datetime__lte=timezone.now(),
        is_processed=False
    )
    
    processed_count = 0
    total_clicks = len(ready_clicks)
    
    # Calculate sleep interval: 10 seconds / number of clicks to process
    # This spreads processing over the 10-second window
    if total_clicks > 0:
        sleep_interval = 10.0 / total_clicks
        logger.info(f"Processing {total_clicks} clicks with {sleep_interval:.2f}s interval between clicks")
    
    for i, click in enumerate(ready_clicks):
        try:
            logger.info(f"Processing click {click.id} for affiliate {click.affiliate_id}")
            
            # Post click to affiliate and get transaction_id
            transaction_id = post_click(click)
            
            # Save transaction_id and mark as processed
            click.transaction_id = transaction_id
            click.is_processed = True
            click.is_processed_datetime = timezone.now()
            click.save()
            
            processed_count += 1
            
            # Sleep between clicks to spread processing over the minute
            if i < total_clicks - 1:  # Don't sleep after the last click
                sleep_time = sleep_interval + random.uniform(-0.1, 0.1)  # Add small random variation
                time.sleep(sleep_time)
            
        except Exception as e:
            logger.error(f"Error processing click {click.id}: {str(e)}")
            continue
    
    logger.info(f"Successfully processed {processed_count} clicks")
    return processed_count

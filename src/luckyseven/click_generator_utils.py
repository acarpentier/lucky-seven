"""
Utility functions for click generator tasks.
"""

from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from .models import Affiliate
import logging

logger = logging.getLogger(__name__)


def get_affiliate_by_id(affiliate_id):
    """
    Fetch affiliate by ID with proper error handling.
    
    Args:
        affiliate_id (str): The affiliate ID to fetch
        
    Returns:
        Affiliate: The affiliate object
        
    Raises:
        ObjectDoesNotExist: If affiliate is not found
    """
    try:
        affiliate = Affiliate.objects.get(affiliate_id=affiliate_id)
        logger.info(f"Processing affiliate: {affiliate.affiliate_id} ({affiliate.affiliate_encoded_value})")
        return affiliate
    except ObjectDoesNotExist:
        logger.error(f"Affiliate with ID '{affiliate_id}' not found")
        raise


def calculate_daily_revenue_goal(affiliate):
    """
    Calculate daily revenue goal based on payout target.
    Payout is 80% of revenue, so revenue goal = payout_target / 0.8
    
    Args:
        affiliate (Affiliate): The affiliate object
        
    Returns:
        Decimal: The calculated daily revenue goal
    """
    daily_revenue_goal = Decimal(str(affiliate.payout_target)) / Decimal('0.8')
    logger.info(f"Daily revenue goal for affiliate {affiliate.affiliate_id}: {daily_revenue_goal}")
    return daily_revenue_goal


def process_affiliate_click_generation(affiliate_id):
    """
    Main function to process click generation for an affiliate.
    
    Args:
        affiliate_id (str): The affiliate ID to process
        
    Returns:
        dict: Processing results with affiliate info and revenue goal
    """
    # Fetch affiliate
    affiliate = get_affiliate_by_id(affiliate_id)
    
    # Calculate daily revenue goal
    daily_revenue_goal = calculate_daily_revenue_goal(affiliate)
    
    return {
        'affiliate': affiliate,
        'daily_revenue_goal': daily_revenue_goal,
        'affiliate_id': affiliate.affiliate_id,
        'affiliate_encoded_value': affiliate.affiliate_encoded_value
    }

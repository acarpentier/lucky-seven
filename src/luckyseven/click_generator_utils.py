"""
Utility functions for click generator tasks.
"""

from decimal import Decimal
from django.core.exceptions import ObjectDoesNotExist
from .models import Affiliate
import csv
import os
import random
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


def load_conversion_costs():
    """
    Load conversion costs from CSV file.
    
    Returns:
        dict: Dictionary mapping country codes to conversion costs
    """
    conversion_costs = {}
    csv_path = os.path.join(os.path.dirname(__file__), 'conversion_cost.csv')
    
    try:
        with open(csv_path, 'r') as file:
            reader = csv.DictReader(file)
            for row in reader:
                country_id = row.get('country_id')
                cost = row.get('cost')
                if country_id and cost:
                    conversion_costs[country_id] = Decimal(cost)
        logger.info(f"Loaded {len(conversion_costs)} conversion costs from CSV")
    except FileNotFoundError:
        logger.warning("Conversion cost CSV file not found")
    except Exception as e:
        logger.error(f"Error loading conversion costs: {str(e)}")
    
    return conversion_costs


def calculate_average_cost_per_conversion(affiliate):
    """
    Calculate average cost per conversion for an affiliate based on their geos.
    
    Args:
        affiliate (Affiliate): The affiliate object with geos list
        
    Returns:
        Decimal: Average cost per conversion across affiliate's geos
    """
    conversion_costs = load_conversion_costs()
    
    if not affiliate.geos or not conversion_costs:
        logger.warning(f"No geos or conversion costs available for affiliate {affiliate.affiliate_id}")
        return Decimal('0.00')
    
    # Get costs for affiliate's geos
    geo_costs = []
    for geo in affiliate.geos:
        if geo in conversion_costs:
            geo_costs.append(conversion_costs[geo])
        else:
            logger.warning(f"No conversion cost found for geo: {geo}")
    
    if not geo_costs:
        logger.warning(f"No conversion costs found for any of affiliate {affiliate.affiliate_id} geos")
        return Decimal('0.00')
    
    # Calculate average
    average_cost = sum(geo_costs) / len(geo_costs)
    logger.info(f"Average cost per conversion for affiliate {affiliate.affiliate_id}: {average_cost}")
    
    return average_cost


def calculate_daily_revenue_runtime(daily_revenue_goal, daily_revenue_deviance):
    """
    Calculate daily revenue with runtime deviance applied.
    
    Args:
        daily_revenue_goal (Decimal): The base daily revenue goal
        daily_revenue_deviance (Decimal): The deviance percentage (e.g., 0.10 for 10%)
        
    Returns:
        Decimal: Daily revenue with deviance applied
    """
    # Generate random deviance between -deviance and +deviance
    deviance_factor = random.uniform(-float(daily_revenue_deviance), float(daily_revenue_deviance))
    
    # Apply deviance to revenue goal
    deviance_multiplier = Decimal('1') + Decimal(str(deviance_factor))
    daily_revenue_runtime = daily_revenue_goal * deviance_multiplier
    
    logger.info(f"Daily revenue runtime: {daily_revenue_runtime} (deviance: {deviance_factor:.2%})")
    return daily_revenue_runtime


def calculate_daily_conversions_needed(daily_revenue_goal, average_cost_per_conversion):
    """
    Calculate how many conversions are needed to reach the daily revenue goal.
    
    Args:
        daily_revenue_goal (Decimal): The daily revenue target
        average_cost_per_conversion (Decimal): Average cost per conversion
        
    Returns:
        int: Number of daily conversions needed
    """
    if average_cost_per_conversion <= 0:
        logger.warning("Average cost per conversion is zero or negative, cannot calculate conversions needed")
        return 0
    
    daily_conversions_needed = daily_revenue_goal / average_cost_per_conversion
    # Round up to ensure we meet the target
    daily_conversions_needed = int(daily_conversions_needed.quantize(Decimal('1'), rounding='ROUND_UP'))
    
    logger.info(f"Daily conversions needed to reach revenue goal: {daily_conversions_needed}")
    return daily_conversions_needed


def calculate_conversion_ratio_runtime(conversion_ratio_target, conversion_ratio_deviance):
    """
    Calculate conversion ratio with runtime deviance applied.
    
    Args:
        conversion_ratio_target (Decimal): The base conversion ratio target (e.g., 2.2 for 2.2%)
        conversion_ratio_deviance (Decimal): The deviance percentage (e.g., 0.4 for 40%)
        
    Returns:
        Decimal: Conversion ratio with deviance applied
    """
    # Generate random deviance between -deviance and +deviance
    deviance_factor = random.uniform(-float(conversion_ratio_deviance), float(conversion_ratio_deviance))
    
    # Apply deviance to conversion ratio target
    deviance_multiplier = Decimal('1') + Decimal(str(deviance_factor))
    conversion_ratio_runtime = conversion_ratio_target * deviance_multiplier
    
    # Ensure we don't go below 0
    if conversion_ratio_runtime < 0:
        conversion_ratio_runtime = Decimal('0.01')  # Minimum 0.01%
    
    logger.info(f"Conversion ratio runtime: {conversion_ratio_runtime}% (deviance: {deviance_factor:.2%})")
    return conversion_ratio_runtime


def calculate_daily_clicks_needed(daily_conversions_needed, conversion_ratio_runtime):
    """
    Calculate how many clicks are needed to support the daily conversions needed.
    
    Args:
        daily_conversions_needed (int): Number of daily conversions needed
        conversion_ratio_runtime (Decimal): The conversion ratio with deviance applied
        
    Returns:
        int: Number of daily clicks needed
    """
    if conversion_ratio_runtime <= 0:
        logger.warning("Conversion ratio runtime is zero or negative, cannot calculate clicks needed")
        return 0
    
    # Convert percentage to decimal (e.g., 2.2% = 0.022)
    conversion_rate = conversion_ratio_runtime / Decimal('100')
    
    # Calculate clicks needed: daily_conversions_needed / conversion_rate
    daily_clicks_needed = Decimal(daily_conversions_needed) / conversion_rate
    
    # Round up to ensure we meet the target
    daily_clicks_needed = int(daily_clicks_needed.quantize(Decimal('1'), rounding='ROUND_UP'))
    
    logger.info(f"Daily clicks needed to support {daily_conversions_needed} conversions: {daily_clicks_needed} (conversion rate: {conversion_ratio_runtime}%)")
    return daily_clicks_needed


def process_affiliate_click_generation(affiliate_id):
    """
    Main function to process click generation for an affiliate.
    
    Args:
        affiliate_id (str): The affiliate ID to process
        
    Returns:
        dict: Processing results with affiliate info, revenue goal, cost data, conversions needed, and clicks needed
    """
    # Fetch affiliate
    affiliate = get_affiliate_by_id(affiliate_id)
    
    # Calculate daily revenue goal
    daily_revenue_goal = calculate_daily_revenue_goal(affiliate)
    
    # Calculate daily revenue with runtime deviance
    daily_revenue_runtime = calculate_daily_revenue_runtime(daily_revenue_goal, affiliate.daily_revenue_deviance)
    
    # Calculate average cost per conversion
    average_cost_per_conversion = calculate_average_cost_per_conversion(affiliate)
    
    # Calculate daily conversions needed (using runtime revenue)
    daily_conversions_needed = calculate_daily_conversions_needed(daily_revenue_runtime, average_cost_per_conversion)
    
    # Calculate conversion ratio with runtime deviance
    conversion_ratio_runtime = calculate_conversion_ratio_runtime(affiliate.conversion_ratio_target, affiliate.conversion_ratio_deviance)
    
    # Calculate daily clicks needed to support conversions (using runtime conversion ratio)
    daily_clicks_needed = calculate_daily_clicks_needed(daily_conversions_needed, conversion_ratio_runtime)
    
    return {
        'affiliate': affiliate,
        'daily_revenue_goal': daily_revenue_goal,
        'daily_revenue_runtime': daily_revenue_runtime,
        'average_cost_per_conversion': average_cost_per_conversion,
        'daily_conversions_needed': daily_conversions_needed,
        'conversion_ratio_runtime': conversion_ratio_runtime,
        'daily_clicks_needed': daily_clicks_needed,
        'affiliate_id': affiliate.affiliate_id,
        'affiliate_encoded_value': affiliate.affiliate_encoded_value
    }

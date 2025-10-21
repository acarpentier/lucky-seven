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
import requests
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any
from django.utils import timezone

logger = logging.getLogger(__name__)

# Click to conversion delay distribution (probability, min_seconds, max_seconds)
# Based on realistic conversion patterns with peak around 50-60 seconds
CONVERSION_DELAY_DISTRIBUTION = [
    (0.15, 30, 40),     # 30-40s
    (0.18, 40, 50),     # 40-50s
    (0.20, 50, 60),     # 50-60s
    (0.15, 60, 70),     # 60-70s
    (0.12, 70, 80),     # 70-80s
    (0.10, 80, 90),     # 80-90s
    (0.08, 90, 100),    # 90-100s
    (0.06, 100, 110),   # 100-110s
    (0.05, 110, 120),   # 110-120s
    (0.04, 120, 130),   # 120-130s
    (0.03, 130, 140),   # 130-140s
    (0.02, 140, 150),   # 140-150s
]


def generate_conversion_delay():
    """
    Generate a realistic conversion delay based on the distribution.
    
    Returns:
        int: Random delay in seconds based on the distribution
    """
    rand = random.random()
    cumulative_prob = 0
    
    for prob, min_seconds, max_seconds in CONVERSION_DELAY_DISTRIBUTION:
        cumulative_prob += prob
        if rand <= cumulative_prob:
            return random.randint(min_seconds, max_seconds)
    
    # Fallback to last range if something goes wrong
    return random.randint(140, 150)


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


def fetch_clicks_from_everflow(from_datetime: str, to_datetime: str, affiliate_geos: List[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch clicks from Everflow API for the given time range.
    Splits large time ranges into 2-minute chunks to avoid 1K limit per request.
    
    Args:
        from_datetime: Start datetime in format "YYYY-MM-DD HH:MM:SS"
        to_datetime: End datetime in format "YYYY-MM-DD HH:MM:SS"
        affiliate_geos: List of country codes to filter by (optional)
    
    Returns:
        List of click records from the API (combined from all chunks)
    """
    # Parse datetime strings
    start_dt = datetime.strptime(from_datetime, "%Y-%m-%d %H:%M:%S")
    end_dt = datetime.strptime(to_datetime, "%Y-%m-%d %H:%M:%S")
    
    # Calculate total time range
    total_minutes = (end_dt - start_dt).total_seconds() / 60
    
    # If time range is 2 minutes or less, make single request
    if total_minutes <= 2:
        return _fetch_clicks_single(from_datetime, to_datetime, affiliate_geos)
    
    # Split into 2-minute chunks
    all_clicks = []
    current_dt = start_dt
    chunk_size = timedelta(minutes=2)
    
    while current_dt < end_dt:
        # Calculate chunk end time (either 2 minutes later or final end time)
        chunk_end_dt = min(current_dt + chunk_size, end_dt)
        
        # Format datetime strings for this chunk
        chunk_from = current_dt.strftime("%Y-%m-%d %H:%M:%S")
        chunk_to = chunk_end_dt.strftime("%Y-%m-%d %H:%M:%S")
        
        # Fetch clicks for this chunk
        chunk_clicks = _fetch_clicks_single(chunk_from, chunk_to, affiliate_geos)
        all_clicks.extend(chunk_clicks)
        
        logger.info(f"🔧 CLICK_GENERATOR: Fetched {len(chunk_clicks)} clicks for chunk {chunk_from} to {chunk_to}")
        
        # Move to next chunk
        current_dt = chunk_end_dt
    
    logger.info(f"🔧 CLICK_GENERATOR: Total clicks fetched from all chunks: {len(all_clicks)}")
    return all_clicks


def _fetch_clicks_single(from_datetime: str, to_datetime: str, affiliate_geos: List[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch clicks from Everflow API for a single time range (2 minutes or less).
    
    Args:
        from_datetime: Start datetime in format "YYYY-MM-DD HH:MM:SS"
        to_datetime: End datetime in format "YYYY-MM-DD HH:MM:SS"
        affiliate_geos: List of country codes to filter by (optional)
    
    Returns:
        List of click records from the API
    """
    url = "https://api.eflow.team/v1/networks/reporting/clicks"
    
    headers = {
        "X-Eflow-API-Key": os.getenv("EVERFLOW_API_KEY"),
        "Content-Type": "application/json"
    }
    
    # Build filters - country and carrier filters
    filters = []
    
    # Add country filters if affiliate_geos provided
    if affiliate_geos:
        for country_code in affiliate_geos:
            filters.append({
                "resource_type": "country_code",
                "filter_id_value": country_code
            })
    
    # Add carrier filter to exclude mobile carrier traffic (0 = non-mobile)
    filters.append({
        "resource_type": "carrier_code",
        "filter_id_value": "0"
    })
    
    payload = {
        "timezone_id": 67,
        "from": from_datetime,
        "to": to_datetime,
        "limit": 10000,
        "query": {
            "filters": filters
        }
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        response.raise_for_status()
        
        data = response.json()
        clicks = data.get("clicks", [])
        return clicks
        
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error fetching clicks from Everflow: {str(e)}")
        raise
    except requests.exceptions.RequestException as e:
        logger.error(f"Request error fetching clicks from Everflow: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching clicks from Everflow: {str(e)}")
        raise


def clean_clicks(clicks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter clicks to ensure unique IPs and quality filtering.
    
    Args:
        clicks: List of clicks from Everflow API
        
    Returns:
        List of filtered clicks with unique IPs and quality checks
    """
    if not clicks:
        return clicks
    
    seen_ips = set()
    filtered_clicks = []
    
    for click in clicks:
        user_ip = click.get("user_ip")
        
        # Skip clicks without IP, with duplicate IPs, or with x in IP (invalid IPv6)
        if not user_ip or user_ip in seen_ips or "x" in user_ip:
            continue
        
        # Get relationship data for quality checks
        relationship = click.get("relationship", {})
        geolocation = relationship.get("geolocation", {})
        device_info = relationship.get("device_information", {})
        
        # Quality filters - skip bad clicks
        if (click.get("is_unique") == 0 or                    # Not unique
            click.get("error_code", 0) != 0 or                # Has error
            click.get("is_test_mode", False) or               # Test mode
            click.get("is_mobile", False) or                  # Mobile traffic
            geolocation.get("is_proxy", False) or             # VPN/proxy
            device_info.get("is_robot", False) or             # Bots
            device_info.get("is_filter", False) or            # Filtered
            float(click.get("forensiq_score", "0")) > 50):    # High fraud score
            continue
            
        # Check if IP already exists in database
        from .models import Click
        existing_click = Click.objects.filter(ip_address=user_ip).exists()
        if existing_click:
            logger.info(f"IP {user_ip} already exists in database, skipping")
            continue
            
        seen_ips.add(user_ip)
        filtered_clicks.append(click)
    
    logger.info(f"Filtered {len(clicks)} clicks down to {len(filtered_clicks)} quality clicks")
    return filtered_clicks


def process_clicks(filtered_clicks: List[Dict[str, Any]], daily_clicks_needed: int, affiliate, conversion_ratio_runtime) -> List[Dict[str, Any]]:
    """
    Process filtered clicks for click generation.
    Reduces clicks to only the amount needed for this hour.
    
    Args:
        filtered_clicks: List of quality filtered clicks
        daily_clicks_needed: Total daily clicks needed
        affiliate: Affiliate object for generating sub1/sub2 values
        
    Returns:
        List of processed click dictionaries
    """
    # Calculate clicks needed for this hour (daily_clicks_needed / 24)
    hourly_clicks_needed = daily_clicks_needed // 24
    
    # Reduce filtered_clicks to only what we need for this hour
    clicks_to_process = filtered_clicks[:hourly_clicks_needed]
    
    logger.info(f"Processing {len(clicks_to_process)} clicks out of {len(filtered_clicks)} available (hourly need: {hourly_clicks_needed})")
    
    processed_clicks = []
    
    for click in clicks_to_process:
        # Extract data from the click
        ip_address = click.get("user_ip")
        # Extract language from relationship data
        relationship = click.get("relationship", {})
        language = relationship.get("http_accept_language", "")
        
        # Extract user agent from relationship data  
        user_agent = relationship.get("http_user_agent", "")
        
        # Create processed click dictionary
        processed_click = {
            "ip_address": ip_address,
            "language": language,
            "user_agent": user_agent,
            "affiliate_id": affiliate.affiliate_id,
            "affiliate_encoded_value": affiliate.affiliate_encoded_value,
            "sub1": affiliate.generate_sub1(),
            "sub2": affiliate.generate_sub2(),
            "to_process": True,
            "to_process_datetime": None,
            "to_convert": False,
            "to_convert_datetime": None,
        }
        
        # Distribute processing time randomly from now to next hour
        now = timezone.now()
        next_hour = now + timedelta(hours=1)
        
        # Generate random datetime between now and next hour
        random_seconds = random.randint(0, 3600)  # 0 to 3600 seconds (1 hour)
        random_datetime = now + timedelta(seconds=random_seconds)
        processed_click["to_process_datetime"] = random_datetime
        
        processed_clicks.append(processed_click)
    
    # Calculate conversions needed based on conversion_ratio_runtime
    conversion_rate = float(conversion_ratio_runtime) / 100
    conversions_needed = int(len(processed_clicks) * conversion_rate)
    
    # Shuffle the processed clicks to randomize which ones get marked for conversion
    random.shuffle(processed_clicks)
    
    # Mark the first N clicks for conversion to match the ratio
    for i in range(conversions_needed):
        processed_clicks[i]["to_convert"] = True
        # Set conversion datetime based on realistic delay distribution
        conversion_delay = generate_conversion_delay()
        conversion_datetime = processed_clicks[i]["to_process_datetime"] + timedelta(seconds=conversion_delay)
        processed_clicks[i]["to_convert_datetime"] = conversion_datetime
    
    logger.info(f"Created {len(processed_clicks)} processed clicks")
    return processed_clicks


def create_clicks(processed_clicks: List[Dict[str, Any]]) -> tuple[int, int]:
    """
    Create Click objects in the database from processed clicks.
    
    Args:
        processed_clicks: List of processed click dictionaries
        
    Returns:
        tuple: (created_count, skipped_count)
    """
    from .models import Click
    from django.db import IntegrityError
    
    created_count = 0
    skipped_count = 0
    
    for click_data in processed_clicks:
        try:
            click = Click.objects.create(
                affiliate_id=click_data["affiliate_id"],
                affiliate_encoded_value=click_data["affiliate_encoded_value"],
                ip_address=click_data["ip_address"],
                user_agent=click_data["user_agent"],
                language=click_data["language"],
                sub1=click_data["sub1"],
                sub2=click_data["sub2"],
                to_process=click_data["to_process"],
                to_process_datetime=click_data["to_process_datetime"],
                to_convert=click_data["to_convert"],
                to_convert_datetime=click_data["to_convert_datetime"]
            )
            created_count += 1
        except IntegrityError as e:
            logger.warning(f"Skipped duplicate IP address: {click_data['ip_address']}")
            skipped_count += 1
            continue
        except Exception as e:
            logger.error(f"Error creating click: {str(e)}")
            continue
    
    logger.info(f"Created {created_count} Click objects in database, skipped {skipped_count} duplicates")
    return created_count, skipped_count

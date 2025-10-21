from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from decimal import Decimal
import json
import random
import string


class Click(models.Model):
    affiliate_id = models.CharField(max_length=50, db_index=True)
    affiliate_encoded_value = models.CharField(max_length=100)

     # Conversion data
    transaction_id = models.CharField(max_length=255, blank=True)
    conversion_id = models.CharField(max_length=255, blank=True)
    
    # Processing flags
    to_process = models.BooleanField(default=False, db_index=True)
    to_process_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    is_processed = models.BooleanField(default=False, db_index=True)
    is_processed_datetime = models.DateTimeField(null=True, blank=True)

    # Conversion flags
    to_convert = models.BooleanField(default=False, db_index=True)
    to_convert_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    is_converted = models.BooleanField(default=False, db_index=True)
    is_converted_datetime = models.DateTimeField(null=True, blank=True)

    # Performance data
    r1_datetime = models.DateTimeField(null=True, blank=True, db_index=True)
    r7_datetime = models.DateTimeField(null=True, blank=True, db_index=True)

    # Properties
    ip_address = models.GenericIPAddressField(null=True, blank=True, unique=True)
    user_agent = models.TextField(blank=True)
    language = models.CharField(max_length=10, blank=True)
    sub1 = models.CharField(max_length=255, blank=True)
    sub2 = models.CharField(max_length=255, blank=True)

    # Tracking timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)


    class Meta:
        db_table = 'clicks'

    def __str__(self):
        return f"Click {self.id} - {self.affiliate_id}"

    def save(self, *args, **kwargs):
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class Affiliate(models.Model):
    # Affiliate ID
    affiliate_id = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Encoded value (e.g., 32L4XJL)
    affiliate_encoded_value = models.CharField(max_length=50, unique=True, db_index=True)
    
    # Money field for payout target
    payout_target = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    
    # Decimal fields for conversion ratios
    conversion_ratio_target = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    conversion_ratio_deviance = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    daily_revenue_deviance = models.DecimalField(max_digits=5, decimal_places=4, default=Decimal('0.0000'))
    
    # JSON field for geos list
    geos = models.JSONField(default=list, help_text="List of country codes")
    
    # Lambda function fields that will be evaluated
    sub1_type_generate = models.TextField(
        help_text="Lambda function as string (e.g., 'lambda: str(random.randint(100000, 999999))')"
    )
    sub2_type_generate = models.TextField(
        help_text="Lambda function as string (e.g., 'lambda: \"\".join(random.choices(string.ascii_lowercase + string.digits, k=32))')"
    )
    
    # Timestamps
    created_at = models.DateTimeField(default=timezone.now, db_index=True)
    updated_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'affiliates'
        verbose_name = 'Affiliate'
        verbose_name_plural = 'Affiliates'
    
    def __str__(self):
        return f"Affiliate {self.affiliate_id} ({self.affiliate_encoded_value})"
    
    def clean(self):
        """Validate the model before saving"""
        super().clean()
        
        # Validate geos list
        if not isinstance(self.geos, list):
            raise ValidationError({'geos': 'Geos must be a list'})
        
        # Test sub1_type_generate lambda
        try:
            func = eval(self.sub1_type_generate)
            result = func()
            if not isinstance(result, str):
                raise ValidationError({'sub1_type_generate': 'Lambda must return a string'})
        except Exception as e:
            raise ValidationError({'sub1_type_generate': f'Invalid lambda function: {str(e)}'})
        
        # Test sub2_type_generate lambda
        try:
            func = eval(self.sub2_type_generate)
            result = func()
            if not isinstance(result, str):
                raise ValidationError({'sub2_type_generate': 'Lambda must return a string'})
        except Exception as e:
            raise ValidationError({'sub2_type_generate': f'Invalid lambda function: {str(e)}'})
    
    def save(self, *args, **kwargs):
        """Override save to run validation"""
        self.full_clean()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
    
    def generate_sub1(self):
        """Generate sub1 value using the lambda function"""
        func = eval(self.sub1_type_generate)
        return func()
    
    def generate_sub2(self):
        """Generate sub2 value using the lambda function"""
        func = eval(self.sub2_type_generate)
        return func()


class Job(models.Model):
    # Job identification
    task_name = models.CharField(max_length=255, db_index=True)
    
    # Job status
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running', db_index=True)
    
    # Execution details
    started_at = models.DateTimeField(default=timezone.now, db_index=True)
    completed_at = models.DateTimeField(null=True, blank=True, db_index=True)
    error_message = models.TextField(blank=True)
    completed_message = models.TextField(blank=True)
    
    class Meta:
        db_table = 'jobs'
        verbose_name = 'Job'
        verbose_name_plural = 'Jobs'
    
    def __str__(self):
        return f"Job {self.task_name} - {self.status}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

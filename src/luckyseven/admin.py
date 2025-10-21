from django.contrib import admin
from .models import Click, Affiliate, Job


@admin.register(Click)
class ClickAdmin(admin.ModelAdmin):
    list_display = ['id', 'affiliate_id', 'affiliate_encoded_value', 'to_process', 'is_processed', 'to_convert', 'is_converted', 'created_at']
    list_filter = ['to_process', 'is_processed', 'to_convert', 'is_converted', 'affiliate_id']
    search_fields = ['affiliate_id', 'affiliate_encoded_value', 'transaction_id', 'conversion_id']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['-created_at']


@admin.register(Affiliate)
class AffiliateAdmin(admin.ModelAdmin):
    list_display = ['affiliate_id', 'affiliate_encoded_value', 'payout_target', 'conversion_ratio_target', 'created_at']
    list_filter = ['created_at']
    search_fields = ['affiliate_id', 'affiliate_encoded_value']
    readonly_fields = ['created_at', 'updated_at']
    ordering = ['affiliate_id']


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['task_name', 'status', 'started_at', 'completed_at']
    list_filter = ['status', 'started_at']
    search_fields = ['task_name', 'error_message', 'completed_message']
    readonly_fields = ['started_at', 'completed_at']
    ordering = ['-started_at']

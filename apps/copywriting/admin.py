from django.contrib import admin
from apps.copywriting.models import CopywritingSession


@admin.register(CopywritingSession)
class CopywritingSessionAdmin(admin.ModelAdmin):
    """Admin interface for CopywritingSession model."""
    
    list_display = [
        'id',
        'project',
        'status',
        'created_at',
        'updated_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['project__title', 'id']
    readonly_fields = ['id', 'created_at', 'updated_at']
    ordering = ['-created_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'project', 'status')
        }),
        ('Data', {
            'fields': ('inputs', 'outputs', 'edits'),
            'classes': ('collapse',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

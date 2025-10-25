from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Q
from apps.search.models import (
    Project,
    SearchRequest,
    SearchResult,
)


class SearchRequestInline(admin.TabularInline):
    """Inline admin for SearchRequests within Project admin."""
    model = SearchRequest
    extra = 0
    fields = ('query', 'language', 'top_results_count', 'status', 'created_at')
    readonly_fields = ('created_at',)
    can_delete = False
    show_change_link = True


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Admin interface for Project model."""
    
    list_display = (
        'title',
        'owner',
        'type',
        'status_badge',
        'search_count',
        'result_count',
        'created_at',
    )
    
    list_filter = (
        'status',
        'type',
        'created_at',
        'updated_at',
    )
    
    search_fields = (
        'title',
        'owner__username',
        'owner__email',
    )
    
    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'search_count',
        'result_count',
        'selected_result_count',
    )
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'owner', 'title', 'type')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Statistics', {
            'fields': (
                'search_count',
                'result_count',
                'selected_result_count',
            ),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SearchRequestInline]
    
    actions = ['mark_as_ready', 'mark_as_failed', 'reset_to_draft']
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'draft': 'gray',
            'searching': 'blue',
            'selecting': 'orange',
            'generating': 'purple',
            'ready': 'green',
            'published': 'darkgreen',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def search_count(self, obj):
        """Count of search requests."""
        return obj.search_requests.count()
    search_count.short_description = 'Searches'
    
    def result_count(self, obj):
        """Count of all search results."""
        return SearchResult.objects.filter(search_request__project=obj).count()
    result_count.short_description = 'Total Results'
    
    def selected_result_count(self, obj):
        """Count of selected search results."""
        return SearchResult.objects.filter(
            search_request__project=obj,
            is_selected=True
        ).count()
    selected_result_count.short_description = 'Selected Results'
    
    @admin.action(description='Mark selected projects as Ready')
    def mark_as_ready(self, request, queryset):
        updated = queryset.update(status='ready')
        self.message_user(request, f'{updated} project(s) marked as ready.')
    
    @admin.action(description='Mark selected projects as Failed')
    def mark_as_failed(self, request, queryset):
        updated = queryset.update(status='failed')
        self.message_user(request, f'{updated} project(s) marked as failed.')
    
    @admin.action(description='Reset selected projects to Draft')
    def reset_to_draft(self, request, queryset):
        updated = queryset.update(status='draft')
        self.message_user(request, f'{updated} project(s) reset to draft.')


class SearchResultInline(admin.TabularInline):
    """Inline admin for SearchResults within SearchRequest admin."""
    model = SearchResult
    extra = 0
    fields = ('title', 'link', 'rank', 'is_selected')
    readonly_fields = ('title', 'link', 'rank')
    can_delete = False
    show_change_link = True


@admin.register(SearchRequest)
class SearchRequestAdmin(admin.ModelAdmin):
    """Admin interface for SearchRequest model."""
    
    list_display = (
        'query',
        'project_link',
        'language',
        'top_results_count',
        'status_badge',
        'result_count',
        'created_at',
        'completed_at',
        'duration',
    )
    
    list_filter = (
        'status',
        'language',
        'created_at',
        'completed_at',
    )
    
    search_fields = (
        'query',
        'project__title',
        'project__owner__username',
    )
    
    readonly_fields = (
        'id',
        'project',
        'created_at',
        'completed_at',
        'result_count',
        'duration',
    )
    
    fieldsets = (
        ('Search Information', {
            'fields': ('id', 'project', 'query', 'language', 'top_results_count', 'params')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Statistics', {
            'fields': ('result_count',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at', 'duration'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [SearchResultInline]
    
    actions = ['mark_as_completed', 'mark_as_failed']
    
    def project_link(self, obj):
        """Link to the related project."""
        url = reverse('admin:search_project_change', args=[obj.project.id])
        return format_html('<a href="{}">{}</a>', url, obj.project.title)
    project_link.short_description = 'Project'
    
    def status_badge(self, obj):
        """Display status with color badge."""
        colors = {
            'pending': 'gray',
            'in_progress': 'blue',
            'completed': 'green',
            'failed': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; '
            'border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def result_count(self, obj):
        """Count of search results."""
        return obj.results.count()
    result_count.short_description = 'Results'
    
    def duration(self, obj):
        """Calculate duration of search."""
        if obj.completed_at and obj.created_at:
            delta = obj.completed_at - obj.created_at
            seconds = delta.total_seconds()
            if seconds < 60:
                return f"{seconds:.1f}s"
            else:
                minutes = seconds / 60
                return f"{minutes:.1f}m"
        return "-"
    duration.short_description = 'Duration'
    
    @admin.action(description='Mark selected requests as Completed')
    def mark_as_completed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='completed', completed_at=timezone.now())
        self.message_user(request, f'{updated} search request(s) marked as completed.')
    
    @admin.action(description='Mark selected requests as Failed')
    def mark_as_failed(self, request, queryset):
        from django.utils import timezone
        updated = queryset.update(status='failed', completed_at=timezone.now())
        self.message_user(request, f'{updated} search request(s) marked as failed.')


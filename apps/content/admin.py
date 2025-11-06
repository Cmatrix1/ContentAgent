from django.contrib import admin
from apps.content.models import Content, VideoDownloadTask, Subtitle, SubtitleBurnTask, WatermarkTask


@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'project',
        'content_type',
        'platform',
        'created_at',
    ]
    list_filter = ['content_type', 'platform', 'created_at']
    search_fields = ['project__title', 'source_url']
    readonly_fields = ['id', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('id', 'project', 'content_type', 'platform')
        }),
        ('Content Details', {
            'fields': ('source_url', 'file_path')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(VideoDownloadTask)
class VideoDownloadTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'content',
        'status',
        'progress',
        'created_at',
        'completed_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['content__title', 'task_id']
    readonly_fields = [
        'id',
        'task_id',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('id', 'content', 'task_id', 'status', 'progress')
        }),
        ('Download Details', {
            'fields': ('download_url', 'file_size', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(Subtitle)
class SubtitleAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'content',
        'language',
        'status',
        'created_at',
        'completed_at',
    ]
    list_filter = ['status', 'language', 'created_at']
    search_fields = ['content__project__title', 'task_id', 'language']
    readonly_fields = [
        'id',
        'task_id',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Subtitle Information', {
            'fields': ('id', 'content', 'language', 'task_id', 'status')
        }),
        ('Subtitle Details', {
            'fields': ('subtitle_text', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(SubtitleBurnTask)
class SubtitleBurnTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'subtitle',
        'status',
        'created_at',
        'completed_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['subtitle__content__project__title', 'task_id']
    readonly_fields = [
        'id',
        'task_id',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('id', 'subtitle', 'task_id', 'status')
        }),
        ('Output Details', {
            'fields': ('output_file_path', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )


@admin.register(WatermarkTask)
class WatermarkTaskAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'content',
        'status',
        'created_at',
        'completed_at',
    ]
    list_filter = ['status', 'created_at']
    search_fields = ['content__project__title', 'task_id']
    readonly_fields = [
        'id',
        'task_id',
        'started_at',
        'completed_at',
        'created_at',
        'updated_at'
    ]
    
    fieldsets = (
        ('Task Information', {
            'fields': ('id', 'content', 'watermark_image', 'task_id', 'status')
        }),
        ('Output Details', {
            'fields': ('output_file_path', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('started_at', 'completed_at', 'created_at', 'updated_at')
        }),
    )

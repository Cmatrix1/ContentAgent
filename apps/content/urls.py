"""
URL routing for content app.
"""
from django.urls import path
from apps.content.views import (
    ContentCreateView,
    VideoDownloadStatusView,
    VideoDownloadTaskDetailView,
    ContentDeleteView,
    SubtitleGenerateView,
    SubtitleListView,
    SubtitleDeleteView,
    SubtitleTranslateView,
    SubtitleBurnView,
    SubtitleBurnStatusView,
    WatermarkCreateView,
    WatermarkStatusView,
)


app_name = 'content'

urlpatterns = [
    # Content Management
    path(
        'projects/<uuid:project_id>/content/create/',
        ContentCreateView.as_view(),
        name='content-create'
    ),
    
    path(
        'projects/<uuid:project_id>/content/delete/',
        ContentDeleteView.as_view(),
        name='content-delete'
    ),
    
    # Video Download
    path(
        'projects/<uuid:project_id>/content/download-status/',
        VideoDownloadStatusView.as_view(),
        name='video-download-status'
    ),
    path(
        'download-tasks/<uuid:task_id>/',
        VideoDownloadTaskDetailView.as_view(),
        name='download-task-detail'
    ),
    
    # Subtitle Management
    path(
        'projects/<uuid:project_id>/subtitles/generate/',
        SubtitleGenerateView.as_view(),
        name='subtitle-generate'
    ),
    
    path(
        'projects/<uuid:project_id>/subtitles/',
        SubtitleListView.as_view(),
        name='subtitle-list'
    ),
    
    path(
        'projects/<uuid:project_id>/subtitles/<uuid:subtitle_id>/delete/',
        SubtitleDeleteView.as_view(),
        name='subtitle-delete'
    ),
    
    path(
        'projects/<uuid:project_id>/subtitles/translate/',
        SubtitleTranslateView.as_view(),
        name='subtitle-translate'
    ),
    
    # Subtitle Burning
    path(
        'projects/<uuid:project_id>/subtitles/<uuid:subtitle_id>/burn/',
        SubtitleBurnView.as_view(),
        name='subtitle-burn'
    ),
    
    path(
        'projects/<uuid:project_id>/burn-tasks/<uuid:burn_task_id>/',
        SubtitleBurnStatusView.as_view(),
        name='subtitle-burn-status'
    ),
    
    # Watermark
    path(
        'projects/<uuid:project_id>/watermark/',
        WatermarkCreateView.as_view(),
        name='watermark-create'
    ),
    
    path(
        'projects/<uuid:project_id>/watermark-tasks/<uuid:watermark_task_id>/',
        WatermarkStatusView.as_view(),
        name='watermark-status'
    ),
]


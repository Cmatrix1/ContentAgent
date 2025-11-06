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
    SubtitleStatusView,
)


app_name = 'content'

urlpatterns = [
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
    
    path(
        'projects/<uuid:project_id>/subtitle/generate/',
        SubtitleGenerateView.as_view(),
        name='subtitle-generate'
    ),
    
    path(
        'projects/<uuid:project_id>/subtitle/status/',
        SubtitleStatusView.as_view(),
        name='subtitle-status'
    ),
]


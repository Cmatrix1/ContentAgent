"""
Selectors for content app - read-only database queries.
"""
from typing import Optional
from django.db.models import QuerySet
from apps.content.models import Content, VideoDownloadTask
from apps.search.models import Project


def get_project_content(project: Project) -> Optional[Content]:
    """
    Get content for a project (one-to-one relationship).
    
    Args:
        project: The project to get content for
    
    Returns:
        Content instance or None if not found
    """
    try:
        return Content.objects.select_related('project').prefetch_related('download_task').get(project=project)
    except Content.DoesNotExist:
        return None


def get_download_task_by_id(task_id: str) -> Optional[VideoDownloadTask]:
    """
    Get video download task by ID.
    
    Args:
        task_id: UUID of the VideoDownloadTask
    
    Returns:
        VideoDownloadTask instance or None if not found
    """
    try:
        return VideoDownloadTask.objects.select_related('content', 'content__project').get(id=task_id)
    except VideoDownloadTask.DoesNotExist:
        return None


def get_download_task_by_content(content: Content) -> Optional[VideoDownloadTask]:
    """
    Get video download task for a content.
    
    Args:
        content: The content to get download task for
    
    Returns:
        VideoDownloadTask instance or None if not found
    """
    try:
        return VideoDownloadTask.objects.get(content=content)
    except VideoDownloadTask.DoesNotExist:
        return None


def list_pending_download_tasks() -> QuerySet[VideoDownloadTask]:
    """
    List all pending download tasks.
    
    Returns:
        QuerySet of VideoDownloadTask instances with status 'pending'
    """
    return VideoDownloadTask.objects.filter(status='pending').select_related('content', 'content__project')


def list_active_download_tasks() -> QuerySet[VideoDownloadTask]:
    """
    List all active download tasks (downloading or processing).
    
    Returns:
        QuerySet of VideoDownloadTask instances with active statuses
    """
    return VideoDownloadTask.objects.filter(
        status__in=['downloading', 'processing']
    ).select_related('content', 'content__project')


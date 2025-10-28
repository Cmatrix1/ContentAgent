import logging
from typing import Optional
from django.utils import timezone
from apps.content.models import Content, VideoDownloadTask
from apps.search.models import Project, SearchResult

logger = logging.getLogger(__name__)


def detect_content_info(url: str) -> dict:
    """
    Detect content type and platform from URL.
    
    Args:
        url: The content URL
    
    Returns:
        Dictionary with content_type and platform
    """
    url_lower = url.lower()
    
    if 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        platform = 'instagram'
        content_type = 'video'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        platform = 'youtube'
        content_type = 'video'
    elif 'linkedin.com' in url_lower:
        platform = 'linkedin'
        content_type = 'video'
    else:
        platform = 'other'
        content_type = 'text'
    
    return {
        'content_type': content_type,
        'platform': platform
    }


def create_content_from_search_result(
    project: Project,
    search_result: SearchResult
) -> Content:
    """
    Create a content entry for a project from a search result.
    
    Args:
        project: The project to associate the content with
        search_result: The search result to create content from
    
    Returns:
        Created Content instance
    
    Raises:
        ValueError: If content already exists for the project
    """

    if hasattr(project, 'content'):
        raise ValueError("Content already exists for this project")
    
    content_info = detect_content_info(search_result.link)
    
    content = Content.objects.create(
        project=project,
        source_url=search_result.link,
        content_type=content_info['content_type'],
        platform=content_info['platform']
    )
    
    logger.info(f"Created content {content.id} for project {project.id} from search result {search_result.id}")
    
    if content_info['content_type'] == 'video':
        create_video_download_task(content)
    
    return content


def create_video_download_task(content: Content) -> VideoDownloadTask:
    """
    Create a video download task for the content.
    
    Args:
        content: The content to create download task for
    
    Returns:
        Created VideoDownloadTask instance
    """
    task = VideoDownloadTask.objects.create(
        content=content,
        status='pending'
    )
    
    logger.info(f"Created video download task {task.id} for content {content.id}")
    
    from apps.content.tasks import download_video_task
    celery_task = download_video_task.delay(str(task.id))
    
    task.task_id = celery_task.id
    task.save(update_fields=['task_id'])
    
    return task


def update_download_task_status(
    task_id: str,
    status: str,
    progress: int = None,
    error_message: str = None,
    download_url: str = None,
    file_size: int = None
) -> Optional[VideoDownloadTask]:
    """
    Update the status of a video download task.
    
    Args:
        task_id: UUID of the VideoDownloadTask
        status: New status
        progress: Download progress (0-100)
        error_message: Error message if failed
        download_url: URL of the downloaded file
        file_size: Size of the file in bytes
    
    Returns:
        Updated VideoDownloadTask instance or None if not found
    """
    task = VideoDownloadTask.objects.get(id=task_id)
    task.status = status
    
    if progress is not None:
        task.progress = progress
    
    if error_message is not None:
        task.error_message = error_message
    
    if download_url is not None:
        task.download_url = download_url
    
    if file_size is not None:
        task.file_size = file_size
    
    if status == 'downloading' and not task.started_at:
        task.started_at = timezone.now()
    
    if status in ['completed', 'failed']:
        task.completed_at = timezone.now()
        task.progress = 100 if status == 'completed' else task.progress

    task.save()
    
    logger.info(f"Updated download task {task_id} status to {status}")
    
    return task



def update_content_file_path(content_id: str, file_path: str) -> Optional[Content]:
    """
    Update the file path of a content.
    
    Args:
        content_id: UUID of the Content
        file_path: Path to the downloaded file
    
    Returns:
        Updated Content instance or None if not found
    """
    content = Content.objects.get(id=content_id)
    content.file_path = file_path
    content.save(update_fields=['file_path'])
    
    logger.info(f"Updated content {content_id} file path to {file_path}")
    
    return content





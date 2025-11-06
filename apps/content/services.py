import logging
from typing import Optional
from django.utils import timezone
from apps.content.models import Content, VideoDownloadTask, Subtitle, SubtitleBurnTask, WatermarkTask
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


def delete_content(content: Content) -> None:
    """
    Delete a content entry and its associated download task.
    
    Args:
        content: The content instance to delete
    
    Returns:
        None
    """
    content_id = content.id
    project_id = content.project.id

    content.delete()
    
    logger.info(f"Deleted content {content_id} for project {project_id}")


def create_subtitle_generation_task(content: Content, language: str = 'original') -> Subtitle:
    """
    Create a subtitle generation task for video content.
    
    Args:
        content: The content to create subtitle task for
        language: Language of the subtitle (default: 'original')
    
    Returns:
        Created Subtitle instance
    
    Raises:
        ValueError: If video is not downloaded for Instagram/LinkedIn platforms
    """
    # For Instagram/LinkedIn, ensure video is downloaded first
    if content.platform in ['instagram', 'linkedin'] and not content.file_path:
        raise ValueError(f"Video must be downloaded before generating subtitles for {content.platform}. Please wait for the download to complete.")
    
    subtitle = Subtitle.objects.create(
        content=content,
        language=language,
        status='pending'
    )
    
    logger.info(f"Created subtitle generation task {subtitle.id} for content {content.id} in {language}")
    
    from apps.content.tasks import generate_subtitle_task
    celery_task = generate_subtitle_task.delay(str(subtitle.id))
    
    subtitle.task_id = celery_task.id
    subtitle.save(update_fields=['task_id'])
    
    return subtitle


def update_subtitle_status(
    subtitle_id: str,
    status: str,
    subtitle_text: str = None,
    error_message: str = None
) -> Optional[Subtitle]:
    """
    Update the status of a subtitle generation task.
    
    Args:
        subtitle_id: UUID of the Subtitle
        status: New status
        subtitle_text: Generated subtitle text
        error_message: Error message if failed
    
    Returns:
        Updated Subtitle instance or None if not found
    """
    subtitle = Subtitle.objects.get(id=subtitle_id)
    subtitle.status = status
    
    if subtitle_text is not None:
        subtitle.subtitle_text = subtitle_text
    
    if error_message is not None:
        subtitle.error_message = error_message
    
    if status == 'generating' and not subtitle.started_at:
        subtitle.started_at = timezone.now()
    
    if status in ['completed', 'failed']:
        subtitle.completed_at = timezone.now()

    subtitle.save()
    
    logger.info(f"Updated subtitle {subtitle_id} status to {status}")
    
    return subtitle


def translate_subtitle_synchronous(source_subtitle: Subtitle, target_language: str) -> Subtitle:
    """
    Translate a subtitle synchronously using AI.
    
    Args:
        source_subtitle: The source subtitle to translate from
        target_language: Target language for translation
    
    Returns:
        Created or updated Subtitle instance with translation
    
    Raises:
        ValueError: If source subtitle is not completed or translation requirements not met
    """
    from django.conf import settings
    from google import genai
    
    if source_subtitle.status != 'completed':
        raise ValueError("Source subtitle must be completed before translation")
    
    if not source_subtitle.subtitle_text:
        raise ValueError("Source subtitle has no text to translate")
    
    # Check if translation already exists for this language
    existing_translation = Subtitle.objects.filter(
        content=source_subtitle.content,
        language=target_language
    ).first()
    
    # If exists and not failed, raise error
    if existing_translation and existing_translation.status != 'failed':
        raise ValueError(f"Subtitle in {target_language} already exists for this content. Delete it first if you want to retranslate.")
    
    # If failed translation exists, reuse it for retry
    if existing_translation and existing_translation.status == 'failed':
        subtitle = existing_translation
        subtitle.status = 'generating'
        subtitle.error_message = None
        subtitle.started_at = timezone.now()
        subtitle.save(update_fields=['status', 'error_message', 'started_at'])
        logger.info(f"Retrying failed translation {subtitle.id} to {target_language}")
    else:
        # Create new subtitle for translation
        subtitle = Subtitle.objects.create(
            content=source_subtitle.content,
            language=target_language,
            status='generating',
            started_at=timezone.now()
        )
        logger.info(f"Created subtitle translation {subtitle.id} from {source_subtitle.id} to {target_language}")
    
    try:
        # Get API key
        api_key = settings.GEMINI_API_KEY
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured in settings")
        
        client = genai.Client(api_key=api_key)
        
        # Prepare translation prompt
        from apps.content.tasks import TRANSLATION_PROMPT_TEMPLATE
        prompt = TRANSLATION_PROMPT_TEMPLATE.format(
            target_language=target_language,
            source_subtitle_text=source_subtitle.subtitle_text
        )
        
        logger.info(f"Calling Gemini API for subtitle translation to {target_language}")
        
        # Call Gemini API
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt]
        )
        
        translated_text = response.text.strip()
        
        # Clean up any markdown formatting if present
        if translated_text.startswith('```'):
            lines = translated_text.split('\n')
            if lines[0].startswith('```'):
                lines = lines[1:]
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            translated_text = '\n'.join(lines)
        
        # Update subtitle with translation
        subtitle.subtitle_text = translated_text
        subtitle.status = 'completed'
        subtitle.completed_at = timezone.now()
        subtitle.save(update_fields=['subtitle_text', 'status', 'completed_at'])
        
        logger.info(f"Subtitle translation {subtitle.id} completed successfully")
        
        return subtitle
        
    except Exception as e:
        # Mark as failed
        subtitle.status = 'failed'
        subtitle.error_message = str(e)
        subtitle.completed_at = timezone.now()
        subtitle.save(update_fields=['status', 'error_message', 'completed_at'])
        
        logger.error(f"Subtitle translation {subtitle.id} failed: {str(e)}", exc_info=True)
        raise


def create_subtitle_burn_task(subtitle: Subtitle) -> SubtitleBurnTask:
    """
    Create a subtitle burn task to hardcode subtitles into video.
    
    Args:
        subtitle: The subtitle to burn into video
    
    Returns:
        Created SubtitleBurnTask instance
    
    Raises:
        ValueError: If subtitle is not completed or video not downloaded
    """
    if subtitle.status != 'completed':
        raise ValueError("Subtitle must be completed before burning into video")
    
    if not subtitle.subtitle_text:
        raise ValueError("Subtitle has no text to burn")
    
    content = subtitle.content
    if not content.file_path:
        raise ValueError("Video file must be downloaded before burning subtitles")
    
    burn_task = SubtitleBurnTask.objects.create(
        subtitle=subtitle,
        status='pending'
    )
    
    logger.info(f"Created subtitle burn task {burn_task.id} for subtitle {subtitle.id}")
    
    from apps.content.tasks import burn_subtitle_task
    celery_task = burn_subtitle_task.delay(str(burn_task.id))
    
    burn_task.task_id = celery_task.id
    burn_task.save(update_fields=['task_id'])
    
    return burn_task


def update_burn_task_status(
    burn_task_id: str,
    status: str,
    output_file_path: str = None,
    error_message: str = None
) -> Optional[SubtitleBurnTask]:
    """
    Update the status of a subtitle burn task.
    
    Args:
        burn_task_id: UUID of the SubtitleBurnTask
        status: New status
        output_file_path: Path to the output video file
        error_message: Error message if failed
    
    Returns:
        Updated SubtitleBurnTask instance or None if not found
    """
    burn_task = SubtitleBurnTask.objects.get(id=burn_task_id)
    burn_task.status = status
    
    if output_file_path is not None:
        burn_task.output_file_path = output_file_path
    
    if error_message is not None:
        burn_task.error_message = error_message
    
    if status == 'processing' and not burn_task.started_at:
        burn_task.started_at = timezone.now()
    
    if status in ['completed', 'failed']:
        burn_task.completed_at = timezone.now()

    burn_task.save()
    
    logger.info(f"Updated burn task {burn_task_id} status to {status}")
    
    return burn_task


def delete_subtitle(subtitle: Subtitle) -> None:
    """
    Delete a subtitle and its associated burn tasks.
    
    Args:
        subtitle: The subtitle instance to delete
    
    Returns:
        None
    """
    subtitle_id = subtitle.id
    subtitle.delete()
    
    logger.info(f"Deleted subtitle {subtitle_id}")


def create_watermark_task(content: Content, watermark_image) -> WatermarkTask:
    """
    Create a watermark task to burn watermark into video.
    
    Args:
        content: The content to add watermark to
        watermark_image: The watermark image file uploaded by user
    
    Returns:
        Created WatermarkTask instance
    
    Raises:
        ValueError: If video not downloaded
    """
    if not content.file_path:
        raise ValueError("Video file must be downloaded before adding watermark")
    
    watermark_task = WatermarkTask.objects.create(
        content=content,
        watermark_image=watermark_image,
        status='pending'
    )
    
    logger.info(f"Created watermark task {watermark_task.id} for content {content.id}")
    
    from apps.content.tasks import burn_watermark_task
    celery_task = burn_watermark_task.delay(str(watermark_task.id))
    
    watermark_task.task_id = celery_task.id
    watermark_task.save(update_fields=['task_id'])
    
    return watermark_task


def update_watermark_task_status(
    watermark_task_id: str,
    status: str,
    output_file_path: str = None,
    error_message: str = None
) -> Optional[WatermarkTask]:
    """
    Update the status of a watermark task.
    
    Args:
        watermark_task_id: UUID of the WatermarkTask
        status: New status
        output_file_path: Path to the output video file
        error_message: Error message if failed
    
    Returns:
        Updated WatermarkTask instance or None if not found
    """
    watermark_task = WatermarkTask.objects.get(id=watermark_task_id)
    watermark_task.status = status
    
    if output_file_path is not None:
        watermark_task.output_file_path = output_file_path
    
    if error_message is not None:
        watermark_task.error_message = error_message
    
    if status == 'processing' and not watermark_task.started_at:
        watermark_task.started_at = timezone.now()
    
    if status in ['completed', 'failed']:
        watermark_task.completed_at = timezone.now()

    watermark_task.save()
    
    logger.info(f"Updated watermark task {watermark_task_id} status to {status}")
    
    return watermark_task






import os
import logging
import requests
import subprocess
from celery import shared_task
from django.conf import settings
from apps.content.models import VideoDownloadTask
from apps.content.services import (
    update_download_task_status,
    update_content_file_path,
)
from apps.content.selectors import get_download_task_by_id

logger = logging.getLogger(__name__)


def detect_platform(url: str) -> str:
    """
    Detect the platform from the URL.
    
    Args:
        url: The video URL
    
    Returns:
        Platform name (instagram, youtube, linkedin, other)
    """
    url_lower = url.lower()
    
    if 'instagram.com' in url_lower or 'instagr.am' in url_lower:
        return 'instagram'
    elif 'youtube.com' in url_lower or 'youtu.be' in url_lower:
        return 'youtube'
    elif 'linkedin.com' in url_lower:
        return 'linkedin'
    else:
        return 'other'


def download_video_from_apihut(video_url: str, platform: str) -> dict:
    """
    Download video using APIHUT.IN API.
    
    Args:
        video_url: The video URL to download
        platform: The platform type (instagram, youtube, linkedin)
    
    Returns:
        Dictionary with download information
    
    Raises:
        Exception if download fails
    """
    api_url = settings.APIHUT_API_URL
    api_key = settings.APIHUT_API_KEY
    
    payload = {
        "video_url": video_url,
        "type": platform
    }
    
    headers = {
    'Accept-Language': 'en-US,en;q=0.9,fa;q=0.8',
    'Connection': 'keep-alive',
    'Content-Type': 'application/json',
    'Origin': 'https://apihut.in',
    'Referer': 'https://apihut.in/docs/api/youtube-instagram-video-downloader',
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-origin',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36',
    'accept': 'application/json',
    'sec-ch-ua': '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
    # 'X-Avatar-Key': api_key
    }
    
    logger.info(f"Requesting video download from APIHUT for {platform}: {video_url}")
    
    response = requests.post(api_url, json=payload, headers=headers, timeout=30)
    response.raise_for_status()
    
    data = response.json()
    
    if not data.get('success'):
        raise Exception(f"APIHUT API request failed: {data}")
    
    return data


def download_video_from_linkedin(video_url: str) -> dict:
    """
    Download video from LinkedIn using yt-dlp.
    
    Args:
        video_url: The LinkedIn video URL
    
    Returns:
        Dictionary with download information
    
    Raises:
        Exception if download fails
    """
    logger.info(f"Downloading LinkedIn video using yt-dlp: {video_url}")
    
    media_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
    os.makedirs(media_dir, exist_ok=True)
    
    output_template = os.path.join(media_dir, '%(id)s.%(ext)s')

    cmd = [
        'yt-dlp',
        '--get-url',
        '--get-filename',
        '-o', output_template,
        video_url
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=True,
            timeout=60
        )
        
        lines = result.stdout.strip().split('\n')
        
        if len(lines) >= 2:
            download_url = lines[0]
            filename = os.path.basename(lines[1])
            
            return {
                'success': 1,
                'url': download_url,
                'filename': filename
            }
        else:
            raise Exception("Failed to extract video URL from yt-dlp")

    except subprocess.CalledProcessError as e:
        logger.error(f"yt-dlp command failed: {e.stderr}")
        raise Exception(f"yt-dlp failed: {e.stderr}")

    except subprocess.TimeoutExpired:
        logger.error("yt-dlp command timed out")
        raise Exception("yt-dlp timed out")


def download_file_from_url(url: str, destination_path: str) -> int:
    """
    Download a file from URL to destination path.
    
    Args:
        url: URL to download from
        destination_path: Local path to save the file
    
    Returns:
        File size in bytes
    
    Raises:
        Exception if download fails
    """
    logger.info(f"Downloading file from {url} to {destination_path}")
    
    response = requests.get(url, stream=True, timeout=300)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    os.makedirs(os.path.dirname(destination_path), exist_ok=True)
    
    with open(destination_path, 'wb') as f:
        downloaded = 0
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                f.write(chunk)
                downloaded += len(chunk)

    logger.info(f"Downloaded {downloaded} bytes to {destination_path}")

    return downloaded


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def download_video_task(self, task_id: str):
    """
    Celery task to download a video.
    
    Args:
        task_id: UUID of the VideoDownloadTask
    
    Returns:
        Dictionary with result information
    """
    logger.info(f"Starting video download task {task_id}")
    
    try:
        task = get_download_task_by_id(task_id)
        
        if not task:
            logger.error(f"VideoDownloadTask {task_id} not found")
            return {'status': 'error', 'message': 'Task not found'}
        
        update_download_task_status(
            task_id=task_id,
            status='downloading',
            progress=10
        )
        
        content = task.content
        video_url = content.source_url
        platform = content.platform
        
        if platform == 'other':
            platform = detect_platform(video_url)
            content.platform = platform
            content.save(update_fields=['platform'])
        
        logger.info(f"Downloading video from {platform}: {video_url}")
        
        download_info = None
        
        if platform == 'linkedin':
            download_info = download_video_from_linkedin(video_url)
        elif platform in ['instagram', 'youtube']:
            download_info = download_video_from_apihut(video_url, platform)
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        update_download_task_status(
            task_id=task_id,
            status='processing',
            progress=30
        )
        
        if platform == 'instagram':
            video_data = download_info.get('data', [])[0] if download_info.get('data') else None
            if not video_data:
                raise Exception("No video data returned from APIHUT")
            
            download_url = video_data.get('url')

        elif platform in {'youtube', 'linkedin'}:
            download_url = download_info.get('url')
        

        if not download_url:
            raise Exception("No download URL found in response")
        
        logger.info(f"Got download URL: {download_url}")

        update_download_task_status(
            task_id=task_id,
            status='downloading',
            progress=50,
            download_url=download_url
        )
        
        media_dir = os.path.join(settings.MEDIA_ROOT, 'videos')
        os.makedirs(media_dir, exist_ok=True)
        
        file_extension = 'mp4'
        filename = f"{content.id}.{file_extension}"
        file_path = os.path.join(media_dir, filename)
        
        file_size = download_file_from_url(download_url, file_path)
        
        relative_path = os.path.join('videos', filename)
        update_content_file_path(str(content.id), relative_path)
        
        update_download_task_status(
            task_id=task_id,
            status='completed',
            progress=100,
            file_size=file_size
        )
        
        logger.info(f"Video download task {task_id} completed successfully")
        
        return {
            'status': 'success',
            'task_id': task_id,
            'file_path': relative_path,
            'file_size': file_size
        }
    
    except Exception as e:
        logger.error(f"Video download task {task_id} failed: {str(e)}", exc_info=True)
        
        update_download_task_status(
            task_id=task_id,
            status='failed',
            error_message=str(e)
        )
        
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for task {task_id}")
            return {
                'status': 'error',
                'task_id': task_id,
                'message': str(e)
            }


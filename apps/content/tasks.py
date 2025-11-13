
import os
import time
import logging
import requests
import subprocess
from celery import shared_task
from django.conf import settings
from google import genai
from google.genai import types
from apps.content.models import VideoDownloadTask, Subtitle, SubtitleBurnTask, WatermarkTask
from apps.content.services import (
    update_download_task_status,
    update_content_file_path,
    update_subtitle_status,
    update_burn_task_status,
    update_watermark_task_status,
)
from apps.content.selectors import get_download_task_by_id, get_subtitle_by_id, get_burn_task_by_id, get_watermark_task_by_id

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


SRT_PROMPT = """
🎯 **OBJECTIVE**
Generate professional-quality subtitles for this video in **SRT format**.  
The subtitles must be accurate, natural, easy to read, and perfectly formatted — ready to use in any video player.

---

### 🧠 ROLE
You are a professional subtitle creator.  
Your job is to create subtitles that feel human-made — with clear language, natural rhythm, and valid SRT formatting.

---

### ⚙️ CORE REQUIREMENTS

#### 1. Language
- Automatically detect the spoken language.  
- Transcribe in that same language (no translation).  
- If multiple languages are spoken, keep each phrase in its original language.

#### 2. Subtitle Readability
- Make subtitles **short, natural, and easy to read**.  
- Each subtitle block should be **4–10 words** (ideally one full thought per line).  
- Split long sentences naturally at pauses or commas.  
- Avoid running multiple sentences in a single subtitle.  
- Each block should be **1–2 short lines max**.  
- Remove unnecessary fillers (“uh”, “um”) unless they carry meaning.  
- Maintain punctuation and capitalization for clarity.

#### 3. Timing Precision
- Each subtitle should last **1–4 seconds** (never longer than 6 seconds).  
- Sync timestamps naturally to speech rhythm.  
- Overlapping timestamps are not allowed.

#### 4. Timestamp Format
Use the exact structure:
```

HH:MM:SS,mmm --> HH:MM:SS,mmm

```
Rules:
- Always use commas `,` before milliseconds (not dots).  
- Milliseconds must have **3 digits**.  
- Always **two digits** for hours, minutes, and seconds.  
- Example:
  ✅ `00:00:00,000 --> 00:00:03,200`  
  ✅ `00:01:12,560 --> 00:01:16,910`

#### 5. SRT Structure
Every subtitle block must strictly follow this format:
```

1
00:00:00,000 --> 00:00:03,200
Subtitle text here.

2
00:00:03,200 --> 00:00:06,800
Next subtitle line.

```

Rules:
- Each block has:
  1. A sequential index (starting at 1)  
  2. A timestamp line  
  3. One or two short text lines  
  4. A blank line after each block  
- Text must always appear **below** the timestamp line (never on the same line).  
- Do **not** include explanations, notes, or metadata.

#### 6. Output Format
- Return **only valid, clean `.srt` text** — ready to save directly.  
- No markdown, code fences, or additional commentary.  
- Ensure line breaks and numbering are clean and consistent.  
- Validate that timestamps are in chronological order and properly aligned.

---

### ✅ EXAMPLE OUTPUT

```

1
00:00:00,000 --> 00:00:02,600
Hey everyone, welcome back!

2
00:00:02,600 --> 00:00:05,300
Today I’ll show you how to use ChatGPT.

3
00:00:05,300 --> 00:00:07,900
Let’s get started.

```

---

### 🧩 FINAL REMINDERS
- Subtitles must look **professional, concise, and human-timed**.  
- **Never attach text to timestamps** (like `01:34:600And`).  
- **Always** use commas in timestamps.  
- **Keep subtitles short, natural, and perfectly formatted.**  
- Output must be **only valid `.srt` text**, nothing else.
"""



@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_subtitle_task(self, subtitle_id: str):
    """
    Celery task to generate subtitles for a video.
    
    Args:
        subtitle_id: UUID of the Subtitle
    
    Returns:
        Dictionary with result information
    """
    logger.info(f"Starting subtitle generation task {subtitle_id}")
    
    try:
        subtitle = get_subtitle_by_id(subtitle_id)
        
        if not subtitle:
            logger.error(f"Subtitle {subtitle_id} not found")
            return {'status': 'error', 'message': 'Subtitle not found'}
        
        update_subtitle_status(
            subtitle_id=subtitle_id,
            status='generating'
        )
        
        content = subtitle.content
        platform = content.platform
        video_url = content.source_url
        
        logger.info(f"Generating subtitle for {platform} video: {video_url}")
        
        
        api_key = settings.GEMINI_API_KEY
        
        if not api_key:
            raise Exception("GEMINI_API_KEY not configured in settings")
        
        client = genai.Client(api_key=api_key)
        
        if platform in ['instagram', 'linkedin']:
            if not content.file_path:
                raise Exception(f"Video file not downloaded for {platform}. Cannot generate subtitles without downloaded video file.")
            
            video_file_path = os.path.join(settings.MEDIA_ROOT, content.file_path)
            
            if not os.path.exists(video_file_path):
                raise Exception(f"Video file not found at path: {video_file_path}")
            
            logger.info(f"Uploading {platform} video to Gemini: {video_file_path}")
            
            myfile = client.files.upload(file=video_file_path)
            logger.info(f"File uploaded - Waiting for processing... (File ID: {myfile.name})")
            
            while myfile.state.name == "PROCESSING":
                logger.info("File still processing...")
                time.sleep(2)
                myfile = client.files.get(name=myfile.name)
            
            if myfile.state.name == "FAILED":
                raise ValueError(f"File processing failed: {myfile.state}")
            
            logger.info(f"File is ACTIVE - Generating subtitles for {platform} video")
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=[myfile, SRT_PROMPT]
            )
            
            subtitle_text = response.text
        
        elif platform == 'youtube':
            logger.info(f"Calling Gemini API for YouTube video: {video_url}")
            
            response = client.models.generate_content(
                model='models/gemini-2.5-flash',
                contents=types.Content(
                    parts=[
                        types.Part(
                            file_data=types.FileData(file_uri=video_url)
                        ),
                        types.Part(text=SRT_PROMPT)
                    ]
                )
            )
            
            subtitle_text = response.text
        
        else:
            raise Exception(f"Unsupported platform: {platform}")
        
        subtitle_text.strip('```srt')
        update_subtitle_status(
            subtitle_id=subtitle_id,
            status='completed',
            subtitle_text=subtitle_text
        )
        
        logger.info(f"Subtitle generation task {subtitle_id} completed successfully")
        
        return {
            'status': 'success',
            'subtitle_id': subtitle_id,
        }
    
    except Exception as e:
        logger.error(f"Subtitle generation task {subtitle_id} failed: {str(e)}", exc_info=True)
        
        update_subtitle_status(
            subtitle_id=subtitle_id,
            status='failed',
            error_message=str(e)
        )
        
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for subtitle task {subtitle_id}")
            return {
                'status': 'error',
                'subtitle_id': subtitle_id,
                'message': str(e)
            }


TRANSLATION_PROMPT_TEMPLATE = """
🎯 **OBJECTIVE**
Translate the following video subtitles into **{target_language}**, producing a smooth, natural, and culturally appropriate version that feels as if it were originally written in {target_language} — while keeping the exact same SRT structure and timing.

---

### 🧠 ROLE
You are a professional subtitle translator and localization expert. Your goal is to create subtitles that sound authentic, natural, and emotionally accurate to native {target_language} viewers.

---

### ⚙️ CORE REQUIREMENTS

#### 1. Natural, Native-Like Translation
- Translate ONLY the dialogue text, not the timestamps or numbering.
- Make the translation **sound natural and conversational**, not word-for-word.
- Adapt idioms, tone, and phrasing to what feels native in {target_language}.
- Preserve meaning, intent, and mood — prioritize clarity and emotional accuracy over literal structure.
- Keep cultural references understandable for {target_language} speakers.
- Keep names, brands, and technical terms in the original language unless translation is widely known or adds clarity.

#### 2. Format Preservation
- Keep ALL timestamps EXACTLY as they are - DO NOT modify timing
- Maintain the exact SRT structure:
  - Sequential numbering (1, 2, 3, ...)
  - Timestamp format: HH:MM:SS,mmm --> HH:MM:SS,mmm
  - Blank lines between subtitle blocks
- Keep line breaks and subtitle segmentation
- Preserve punctuation style appropriate for {target_language}

#### 3. Text Length & Readability
- Keep translations concise and readable
- Try to match the original text length when possible
- If translation is longer, you may split into 2 short lines
- Ensure subtitles remain easy to read at original timing

#### 4. Output Format
- No markdown, code fences, or explanations
- Translate for naturalness, not literal accuracy.
- Keep meaning, emotion, and tone intact.
- Maintain exact SRT formatting and timestamps.
- Output should look like a professionally translated subtitle file.

---

### ✅ EXAMPLE

**Original (English):**
```
1
00:00:00,000 --> 00:00:03,200
Hey everyone, welcome back!

2
00:00:03,200 --> 00:00:06,800
Today I'll show you something cool.
```

**Translated (Persian):**
```
1
00:00:00,000 --> 00:00:03,200
سلام به همه، خوش برگشتید!

2
00:00:03,200 --> 00:00:06,800
امروز یه چیز جالب نشونتون میدم.
```

---

### 🧩 FINAL REMINDERS
- ONLY translate the subtitle text, NOT the timestamps or numbers
- Maintain the exact same SRT structure
- Output must be clean, valid SRT format
- Use natural, native {target_language}

---

### SOURCE SUBTITLE TO TRANSLATE:

{source_subtitle_text}
"""




@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def burn_subtitle_task(self, burn_task_id: str):
    """
    Celery task to burn (hardcode) subtitles into video using ffmpeg.
    
    Args:
        burn_task_id: UUID of the SubtitleBurnTask
    
    Returns:
        Dictionary with result information
    """
    logger.info(f"Starting subtitle burn task {burn_task_id}")
    
    try:
        burn_task = get_burn_task_by_id(burn_task_id)
        
        if not burn_task:
            logger.error(f"Burn task {burn_task_id} not found")
            return {'status': 'error', 'message': 'Burn task not found'}
        
        update_burn_task_status(
            burn_task_id=burn_task_id,
            status='processing'
        )
        
        subtitle = burn_task.subtitle
        content = subtitle.content
        
        if not content.file_path:
            raise Exception("Video file not found")
        
        if not subtitle.subtitle_text:
            raise Exception("Subtitle text is empty")
        
        video_file_path = os.path.join(settings.MEDIA_ROOT, content.file_path)
        
        if not os.path.exists(video_file_path):
            raise Exception(f"Video file not found at path: {video_file_path}")
        
        subtitle_dir = os.path.join(settings.MEDIA_ROOT, 'subtitles')
        os.makedirs(subtitle_dir, exist_ok=True)
        
        subtitle_filename = f"{burn_task_id}.srt"
        subtitle_file_path = os.path.join(subtitle_dir, subtitle_filename)
        
        try:
            with open(subtitle_file_path, 'w', encoding='utf-8') as f:
                f.write(subtitle.subtitle_text)
            
            output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'subtitled')
            os.makedirs(output_dir, exist_ok=True)
            
            output_filename = f"{content.id}_{subtitle.language}.mp4"
            output_file_path = os.path.join(output_dir, output_filename)
    
            subtitle_path_escaped = subtitle_file_path.replace('\\', '/')

            force_style = (
                "FontName=Arial,"
                "FontSize=24,"
                "PrimaryColour=&H00FFFFFF,"
                "OutlineColour=&H00000000,"
                "BorderStyle=3,"
                "Outline=2,"
                "Shadow=1"
            )

            filter_string = f"subtitles={subtitle_path_escaped}:force_style='{force_style}'"

            cmd = [
                'ffmpeg',
                '-i', video_file_path,
                '-vf', filter_string,
                '-c:a', 'copy',
                '-y',
                output_file_path
            ]

            logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600  
            )
            
            if result.returncode != 0:
                raise Exception(f"ffmpeg failed: {result.stderr}")
            
            # Calculate relative path
            relative_output_path = os.path.join('videos', 'subtitled', output_filename)
            
            # Update content file path to point to the new video with burned subtitles
            update_content_file_path(str(content.id), relative_output_path)
            
            update_burn_task_status(
                burn_task_id=burn_task_id,
                status='completed',
                output_file_path=relative_output_path
            )
            
            logger.info(f"Subtitle burn task {burn_task_id} completed successfully")
            
            return {
                'status': 'success',
                'burn_task_id': burn_task_id,
                'output_file_path': relative_output_path
            }
        
        finally:
            # Clean up temporary subtitle file
            if os.path.exists(subtitle_file_path):
                os.remove(subtitle_file_path)
    
    except Exception as e:
        logger.error(f"Subtitle burn task {burn_task_id} failed: {str(e)}", exc_info=True)
        
        update_burn_task_status(
            burn_task_id=burn_task_id,
            status='failed',
            error_message=str(e)
        )
        
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for burn task {burn_task_id}")
            return {
                'status': 'error',
                'burn_task_id': burn_task_id,
                'message': str(e)
            }


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def burn_watermark_task(self, watermark_task_id: str):
    """
    Celery task to burn (hardcode) watermark into video using ffmpeg.
    
    Args:
        watermark_task_id: UUID of the WatermarkTask
    
    Returns:
        Dictionary with result information
    """
    logger.info(f"Starting watermark burn task {watermark_task_id}")
    
    try:
        watermark_task = get_watermark_task_by_id(watermark_task_id)
        
        if not watermark_task:
            logger.error(f"Watermark task {watermark_task_id} not found")
            return {'status': 'error', 'message': 'Watermark task not found'}
        
        update_watermark_task_status(
            watermark_task_id=watermark_task_id,
            status='processing'
        )
        
        content = watermark_task.content
        
        if not content.file_path:
            raise Exception("Video file not found")
        
        if not watermark_task.watermark_image:
            raise Exception("Watermark image is missing")
        

        video_file_path = os.path.join(settings.MEDIA_ROOT, content.file_path)
        
        if not os.path.exists(video_file_path):
            raise Exception(f"Video file not found at path: {video_file_path}")

        watermark_image_path = os.path.join(settings.MEDIA_ROOT, watermark_task.watermark_image.name)
        
        if not os.path.exists(watermark_image_path):
            raise Exception(f"Watermark image not found at path: {watermark_image_path}")
        
        # Create output file path
        output_dir = os.path.join(settings.MEDIA_ROOT, 'videos', 'watermarked')
        os.makedirs(output_dir, exist_ok=True)
        
        output_filename = f"{content.id}_watermarked.mp4"
        output_file_path = os.path.join(output_dir, output_filename)

        cmd = [
            'ffmpeg',
            '-i', video_file_path,
            '-i', watermark_image_path,
            '-filter_complex', '[1:v]format=rgba[watermark];[0:v][watermark]overlay=W-w-10:H-h-10',
            '-c:a', 'copy',  
            '-y', 
            output_file_path
        ]
        
        logger.info(f"Running ffmpeg command: {' '.join(cmd)}")
        
        # Run ffmpeg command
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=600  # 10 minutes timeout
        )
        
        if result.returncode != 0:
            raise Exception(f"ffmpeg failed: {result.stderr}")
        
        # Calculate relative path
        relative_output_path = os.path.join('videos', 'watermarked', output_filename)
        
        # Update content file path to point to the new video with burned watermark
        update_content_file_path(str(content.id), relative_output_path)
        
        update_watermark_task_status(
            watermark_task_id=watermark_task_id,
            status='completed',
            output_file_path=relative_output_path
        )
        
        logger.info(f"Watermark burn task {watermark_task_id} completed successfully")
        
        return {
            'status': 'success',
            'watermark_task_id': watermark_task_id,
            'output_file_path': relative_output_path
        }
    
    except Exception as e:
        logger.error(f"Watermark burn task {watermark_task_id} failed: {str(e)}", exc_info=True)
        
        update_watermark_task_status(
            watermark_task_id=watermark_task_id,
            status='failed',
            error_message=str(e)
        )
        
        try:
            raise self.retry(exc=e)
        except self.MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for watermark burn task {watermark_task_id}")
            return {
                'status': 'error',
                'watermark_task_id': watermark_task_id,
                'message': str(e)
            }


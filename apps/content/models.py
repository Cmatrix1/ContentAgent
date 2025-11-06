import uuid
from django.db import models
from django.conf import settings
from apps.search.models import Project


class Content(models.Model):
    """
    Model to store content saved by users from search results.
    One-to-one relationship with Project.
    """
    CONTENT_TYPE_CHOICES = [
        ('video', 'Video'),
        ('text', 'Text'),
        ('image', 'Image'),
    ]
    
    PLATFORM_CHOICES = [
        ('instagram', 'Instagram'),
        ('youtube', 'YouTube'),
        ('linkedin', 'LinkedIn'),
        ('other', 'Other'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.OneToOneField(
        Project,
        on_delete=models.CASCADE,
        related_name='content'
    )
    source_url = models.URLField(max_length=1000)
    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPE_CHOICES,
        default='text'
    )
    platform = models.CharField(
        max_length=50,
        choices=PLATFORM_CHOICES,
        default='other'
    )
    file_path = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Contents'
    
    def __str__(self):
        return f"{self.project.title} - {self.content_type}"


class VideoDownloadTask(models.Model):
    """
    Model to track video download tasks status.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('downloading', 'Downloading'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.OneToOneField(
        Content,
        on_delete=models.CASCADE,
        related_name='download_task'
    )
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    progress = models.PositiveIntegerField(default=0)  # 0-100
    error_message = models.TextField(blank=True, null=True)
    download_url = models.URLField(max_length=10000, blank=True, null=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # in bytes
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Download Task {self.id} - {self.status}"


class Subtitle(models.Model):
    """
    Model to store subtitles for video content.
    Each content can have multiple subtitles in different languages.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='subtitles'
    )
    language = models.CharField(
        max_length=50,
        default='original',
        help_text='Language of the subtitle (e.g., original, persian, english, spanish)'
    )
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    subtitle_text = models.TextField(blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['content', 'language']
    
    def __str__(self):
        return f"Subtitle {self.id} - {self.language} - {self.status}"


class SubtitleBurnTask(models.Model):
    """
    Model to track subtitle burning (hardcoding) into video tasks.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    subtitle = models.ForeignKey(
        Subtitle,
        on_delete=models.CASCADE,
        related_name='burn_tasks'
    )
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    output_file_path = models.CharField(max_length=500, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Burn Task {self.id} - {self.status}"


class WatermarkTask(models.Model):
    """
    Model to track watermark burning into video tasks.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    content = models.ForeignKey(
        Content,
        on_delete=models.CASCADE,
        related_name='watermark_tasks'
    )
    watermark_image = models.ImageField(
        upload_to='watermarks/',
        help_text='Watermark image to burn into video (PNG with transparency recommended)'
    )
    task_id = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    output_file_path = models.CharField(max_length=500, blank=True, null=True)
    error_message = models.TextField(blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    completed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Watermark Task {self.id} - {self.status}"

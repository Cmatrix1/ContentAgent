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


import uuid
from django.db import models
from django.conf import settings

from apps.search.constants import get_default_platforms


class Project(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20,
        choices=[
            ("video", "Video"),
            ("text", "Text"),
        ],
        default="text",
    )
    status = models.CharField(
        max_length=50,
        choices=[
            ("draft", "Draft"),
            ("searching", "Searching"),
            ("selecting", "Selecting Sources"),
            ("generating", "Generating"),
            ("ready", "Ready"),
            ("published", "Published"),
            ("failed", "Failed"),
        ],
        default="draft",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class SearchRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="search_requests")
    query = models.CharField(max_length=255)
    language = models.CharField(max_length=50, default="en")
    top_results_count = models.PositiveIntegerField(default=10)
    params = models.JSONField(default=dict, blank=True)
    platforms = models.JSONField(default=get_default_platforms, blank=True)
    status = models.CharField(
        max_length=30,
        choices=[
            ("pending", "Pending"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.project.title} - {self.query}"


class SearchResult(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    search_request = models.ForeignKey(SearchRequest, on_delete=models.CASCADE, related_name="results")
    title = models.CharField(max_length=512)
    link = models.URLField(max_length=1000)
    snippet = models.TextField(blank=True)
    rank = models.PositiveIntegerField(default=0)
    is_selected = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict, blank=True)
    fetched_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["rank"]

    def __str__(self):
        return f"{self.title[:60]}..."



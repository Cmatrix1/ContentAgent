import uuid
from django.db import models
from apps.search.models import Project


class CopywritingSession(models.Model):
    """
    Model to store AI-generated marketing copy for projects.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='copywriting_sessions'
    )
    inputs = models.JSONField(default=dict, blank=True)
    outputs = models.JSONField(default=dict, blank=True)
    edits = models.JSONField(default=dict, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Copywriting Sessions'
    
    def __str__(self):
        return f"{self.project.title} - {self.status}"
    
    def get_final_outputs(self) -> dict:
        """
        Merge outputs and edits, with edits overwriting outputs.
        
        Returns:
            Dictionary with final merged outputs
        """
        if isinstance(self.outputs, list):
            outputs = self.outputs[0] if self.outputs and isinstance(self.outputs[0], dict) else {}
        else:
            outputs = self.outputs if isinstance(self.outputs, dict) else {}
        
        edits = self.edits if isinstance(self.edits, dict) else {}
        
        final = outputs.copy()
        final.update(edits)
        return final

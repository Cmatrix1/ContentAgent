from rest_framework import serializers
from apps.content.models import Content, VideoDownloadTask


class ContentSerializer(serializers.ModelSerializer):
    """
    Serializer for Content model.
    """
    download_status = serializers.SerializerMethodField()
    project_title = serializers.CharField(source='project.title', read_only=True)
    
    class Meta:
        model = Content
        fields = [
            'id',
            'project',
            'project_title',
            'source_url',
            'content_type',
            'platform',
            'file_path',
            'download_status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'file_path']
    
    def get_download_status(self, obj):
        """Get download task status if exists."""
        try:
            task = obj.download_task
            return {
                'task_id': str(task.id),
                'status': task.status,
                'progress': task.progress,
                'error_message': task.error_message,
            }
        except VideoDownloadTask.DoesNotExist:
            return None


class ContentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating content from a search result.
    """
    search_result_id = serializers.UUIDField()


class VideoDownloadTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for VideoDownloadTask model.
    """
    content_title = serializers.CharField(source='content.title', read_only=True)
    content_url = serializers.URLField(source='content.source_url', read_only=True)
    
    class Meta:
        model = VideoDownloadTask
        fields = [
            'id',
            'content',
            'content_title',
            'content_url',
            'task_id',
            'status',
            'progress',
            'error_message',
            'download_url',
            'file_size',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'task_id',
            'status',
            'progress',
            'error_message',
            'download_url',
            'file_size',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]


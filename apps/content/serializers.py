from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field
from apps.content.models import Content, VideoDownloadTask, Subtitle, SubtitleBurnTask, WatermarkTask


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
    
    @extend_schema_field(serializers.DictField(allow_null=True))
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


class SubtitleSerializer(serializers.ModelSerializer):
    """
    Serializer for Subtitle model.
    """
    content_url = serializers.URLField(source='content.source_url', read_only=True)
    platform = serializers.CharField(source='content.platform', read_only=True)
    project_title = serializers.CharField(source='content.project.title', read_only=True)
    
    class Meta:
        model = Subtitle
        fields = [
            'id',
            'content',
            'language',
            'content_url',
            'platform',
            'project_title',
            'task_id',
            'status',
            'subtitle_text',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'task_id',
            'status',
            'subtitle_text',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]


class SubtitleTranslateSerializer(serializers.Serializer):
    """
    Serializer for subtitle translation request.
    """
    source_subtitle_id = serializers.UUIDField(
        help_text='UUID of the source subtitle to translate from'
    )
    target_language = serializers.CharField(
        default='persian',
        help_text='Target language for translation (e.g., persian, english, spanish)'
    )


class SubtitleBurnTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for SubtitleBurnTask model.
    """
    subtitle_language = serializers.CharField(source='subtitle.language', read_only=True)
    content_id = serializers.UUIDField(source='subtitle.content.id', read_only=True)
    
    class Meta:
        model = SubtitleBurnTask
        fields = [
            'id',
            'subtitle',
            'subtitle_language',
            'content_id',
            'task_id',
            'status',
            'output_file_path',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'task_id',
            'status',
            'output_file_path',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]


class WatermarkTaskSerializer(serializers.ModelSerializer):
    """
    Serializer for WatermarkTask model.
    """
    content_id = serializers.UUIDField(source='content.id', read_only=True)
    watermark_image_url = serializers.SerializerMethodField()
    
    class Meta:
        model = WatermarkTask
        fields = [
            'id',
            'content',
            'content_id',
            'watermark_image',
            'watermark_image_url',
            'task_id',
            'status',
            'output_file_path',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'task_id',
            'status',
            'output_file_path',
            'error_message',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
    
    def get_watermark_image_url(self, obj):
        """Get the full URL of the watermark image."""
        if obj.watermark_image:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.watermark_image.url)
            return obj.watermark_image.url
        return None


class WatermarkCreateSerializer(serializers.Serializer):
    """
    Serializer for creating watermark task with image upload.
    """
    watermark_image = serializers.ImageField(
        help_text='Watermark image file (PNG with transparency recommended)',
        required=True
    )


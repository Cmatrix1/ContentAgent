from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.types import OpenApiTypes
from apps.content.serializers import (
    ContentSerializer,
    ContentCreateSerializer,
    VideoDownloadTaskSerializer,
)



content_create_schema = extend_schema(
    operation_id='create_content',
    summary='Create content from a search result',
    description=(
        'Creates content for a project based on a selected search result. '
        'If the content type is video, this will automatically trigger a video download task. '
        'Each project can only have one content item.'
    ),
    tags=['Content'],
    request=ContentCreateSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to create content for',
            required=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=ContentSerializer,
            description='Content created successfully',
            examples=[
                OpenApiExample(
                    'Video Content Created',
                    value={
                        'id': '990e8400-e29b-41d4-a716-446655440000',
                        'project': '550e8400-e29b-41d4-a716-446655440000',
                        'project_title': 'My Video Project',
                        'source_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'content_type': 'video',
                        'platform': 'youtube',
                        'file_path': None,
                        'download_status': {
                            'task_id': 'aa0e8400-e29b-41d4-a716-446655440000',
                            'status': 'pending',
                            'progress': 0,
                            'error_message': None,
                        },
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:00:00Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Text Content Created',
                    value={
                        'id': '990e8400-e29b-41d4-a716-446655440000',
                        'project': '550e8400-e29b-41d4-a716-446655440000',
                        'project_title': 'My Blog Post',
                        'source_url': 'https://example.com/article',
                        'content_type': 'text',
                        'platform': 'other',
                        'file_path': None,
                        'download_status': None,
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:00:00Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data, content already exists, or search result mismatch',
            examples=[
                OpenApiExample(
                    'Content Already Exists',
                    value={
                        'error': 'Content already exists for this project.',
                    },
                ),
                OpenApiExample(
                    'Search Result Mismatch',
                    value={
                        'error': 'Search result does not belong to this project.',
                    },
                ),
                OpenApiExample(
                    'Validation Error',
                    value={
                        'search_result_id': ['This field is required.'],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or search result not found',
            examples=[
                OpenApiExample(
                    'Project Not Found',
                    value={
                        'error': 'Project not found or access denied.',
                    },
                ),
                OpenApiExample(
                    'Search Result Not Found',
                    value={
                        'error': 'Search result not found.',
                    },
                ),
            ],
        ),
    },
    examples=[
        OpenApiExample(
            'Create Content from Search Result',
            value={
                'search_result_id': '770e8400-e29b-41d4-a716-446655440000',
            },
            request_only=True,
        ),
    ],
)



# VIDEO DOWNLOAD ENDPOINTS SCHEMAS
video_download_status_schema = extend_schema(
    operation_id='get_video_download_status',
    summary='Get video download status for a project',
    description=(
        'Retrieves the current status of the video download task for a specific project. '
        'Only applicable for projects with video content.'
    ),
    tags=['Content'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to check download status for',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=VideoDownloadTaskSerializer,
            description='Download status retrieved successfully',
            examples=[
                OpenApiExample(
                    'Download Pending',
                    value={
                        'id': 'aa0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_title': None,
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'task_id': 'celery-task-id-12345',
                        'status': 'pending',
                        'progress': 0,
                        'error_message': None,
                        'download_url': None,
                        'file_size': None,
                        'started_at': None,
                        'completed_at': None,
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:00:00Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Download In Progress',
                    value={
                        'id': 'aa0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_title': None,
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'task_id': 'celery-task-id-12345',
                        'status': 'downloading',
                        'progress': 45,
                        'error_message': None,
                        'download_url': 'https://api.service.com/download/abc123',
                        'file_size': 15728640,
                        'started_at': '2024-01-15T11:01:00Z',
                        'completed_at': None,
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:02:30Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Download Completed',
                    value={
                        'id': 'aa0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_title': None,
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'task_id': 'celery-task-id-12345',
                        'status': 'completed',
                        'progress': 100,
                        'error_message': None,
                        'download_url': 'https://api.service.com/download/abc123',
                        'file_size': 31457280,
                        'started_at': '2024-01-15T11:01:00Z',
                        'completed_at': '2024-01-15T11:05:00Z',
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:05:00Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Download Failed',
                    value={
                        'id': 'aa0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_title': None,
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'task_id': 'celery-task-id-12345',
                        'status': 'failed',
                        'progress': 0,
                        'error_message': 'Video unavailable or private',
                        'download_url': None,
                        'file_size': None,
                        'started_at': '2024-01-15T11:01:00Z',
                        'completed_at': None,
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:01:30Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Content is not a video',
            examples=[
                OpenApiExample(
                    'Not a Video',
                    value={
                        'error': 'Content is not a video.',
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or content not found',
            examples=[
                OpenApiExample(
                    'Project Not Found',
                    value={
                        'error': 'Project not found or access denied.',
                    },
                ),
                OpenApiExample(
                    'Content Not Found',
                    value={
                        'error': 'No content found for this project.',
                    },
                ),
            ],
        ),
    },
)


video_download_task_detail_schema = extend_schema(
    operation_id='get_download_task_details',
    summary='Get details of a specific download task',
    description=(
        'Retrieves detailed information about a specific video download task by its task ID. '
        'Access is restricted to the owner of the project.'
    ),
    tags=['Content'],
    parameters=[
        OpenApiParameter(
            name='task_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the download task',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=VideoDownloadTaskSerializer,
            description='Download task details retrieved successfully',
            examples=[
                OpenApiExample(
                    'Task Details',
                    value={
                        'id': 'aa0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_title': None,
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'task_id': 'celery-task-id-12345',
                        'status': 'processing',
                        'progress': 75,
                        'error_message': None,
                        'download_url': 'https://api.service.com/download/abc123',
                        'file_size': 31457280,
                        'started_at': '2024-01-15T11:01:00Z',
                        'completed_at': None,
                        'created_at': '2024-01-15T11:00:00Z',
                        'updated_at': '2024-01-15T11:03:45Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        403: OpenApiResponse(
            description='Access denied - User does not own the project',
            examples=[
                OpenApiExample(
                    'Access Denied',
                    value={
                        'error': 'Access denied.',
                    },
                ),
            ],
        ),
        404: OpenApiResponse(
            description='Download task not found',
            examples=[
                OpenApiExample(
                    'Task Not Found',
                    value={
                        'error': 'Download task not found.',
                    },
                ),
            ],
        ),
    },
)


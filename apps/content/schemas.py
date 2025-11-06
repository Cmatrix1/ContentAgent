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
    SubtitleSerializer,
    SubtitleTranslateSerializer,
    SubtitleBurnTaskSerializer,
    WatermarkTaskSerializer,
    WatermarkCreateSerializer,
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


content_delete_schema = extend_schema(
    operation_id='delete_content',
    summary='Delete content for a project',
    description=(
        'Deletes the content associated with a specific project. '
        'This will also delete any associated video download tasks. '
        'Access is restricted to the owner of the project.'
    ),
    tags=['Content'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project whose content to delete',
            required=True,
        ),
    ],
    responses={
        204: OpenApiResponse(
            description='Content deleted successfully',
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


subtitle_generate_schema = extend_schema(
    operation_id='generate_subtitle',
    summary='Generate subtitles for video content',
    description=(
        'Generates subtitles for a project\'s video content. '
        'Uses Google Gemini API to create SRT format subtitles. '
        'For Instagram and LinkedIn videos, the video must be downloaded first. '
        'If subtitle generation previously failed, this endpoint will allow regeneration.'
    ),
    tags=['Subtitles'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to generate subtitles for',
            required=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=SubtitleSerializer,
            description='Subtitle generation task created successfully',
            examples=[
                OpenApiExample(
                    'Subtitle Generation Started',
                    value={
                        'id': 'bb0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'platform': 'youtube',
                        'project_title': 'My Video Project',
                        'task_id': 'celery-task-id-67890',
                        'status': 'pending',
                        'subtitle_text': None,
                        'error_message': None,
                        'started_at': None,
                        'completed_at': None,
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:00:00Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Content is not a video, subtitle already exists, or video not downloaded',
            examples=[
                OpenApiExample(
                    'Not a Video',
                    value={
                        'error': 'Content is not a video. Subtitles can only be generated for video content.',
                    },
                ),
                OpenApiExample(
                    'Subtitle Already Exists',
                    value={
                        'error': 'Subtitle already exists for this content.',
                    },
                ),
                OpenApiExample(
                    'Video Not Downloaded',
                    value={
                        'error': 'Video must be downloaded before generating subtitles for instagram. Please wait for the download to complete.',
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


subtitle_list_schema = extend_schema(
    operation_id='list_subtitles',
    summary='List all subtitles for a project',
    description=(
        'Retrieves all subtitles for a project\'s video content. '
        'Returns subtitles in all languages that have been generated or translated.'
    ),
    tags=['Subtitles'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to list subtitles for',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=SubtitleSerializer(many=True),
            description='Subtitles list retrieved successfully',
        ),
        400: OpenApiResponse(
            description='Bad request - Content is not a video',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or content not found',
        ),
    },
)


subtitle_delete_schema = extend_schema(
    operation_id='delete_subtitle',
    summary='Delete a specific subtitle',
    description=(
        'Deletes a subtitle and all its associated burn tasks. '
        'This action cannot be undone.'
    ),
    tags=['Subtitles'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='subtitle_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the subtitle to delete',
            required=True,
        ),
    ],
    responses={
        204: OpenApiResponse(
            description='Subtitle deleted successfully',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        403: OpenApiResponse(
            description='Subtitle does not belong to this project'
        ),
        404: OpenApiResponse(
            description='Project or subtitle not found',
        ),
    },
)


subtitle_translate_schema = extend_schema(
    operation_id='translate_subtitle',
    summary='Translate subtitle to another language (synchronous)',
    description=(
        'Translates an existing subtitle to a different language using AI synchronously. '
        'The translation preserves the SRT format and timing. '
        'Default target language is Persian. '
        'This is a synchronous operation that returns the completed translation immediately. '
        'If a translation to the target language already exists and has failed, it will retry the translation. '
        'If the translation exists and is not failed, an error will be returned.'
    ),
    tags=['Subtitles'],
    request=SubtitleTranslateSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=SubtitleSerializer,
            description='Translation completed successfully',
            examples=[
                OpenApiExample(
                    'Translation Completed',
                    value={
                        'id': 'cc0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'language': 'persian',
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'platform': 'youtube',
                        'project_title': 'My Video Project',
                        'task_id': None,
                        'status': 'completed',
                        'subtitle_text': '1\n00:00:00,000 --> 00:00:03,000\nمتن زیرنویس اول اینجاست',
                        'error_message': None,
                        'started_at': '2024-01-15T13:00:00Z',
                        'completed_at': '2024-01-15T13:00:15Z',
                        'created_at': '2024-01-15T13:00:00Z',
                        'updated_at': '2024-01-15T13:00:15Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data, translation requirements not met, or translation already exists',
            examples=[
                OpenApiExample(
                    'Translation Already Exists',
                    value={
                        'error': 'Subtitle in persian already exists for this content. Delete it first if you want to retranslate.',
                    },
                ),
                OpenApiExample(
                    'Source Not Completed',
                    value={
                        'error': 'Source subtitle must be completed before translation',
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        403: OpenApiResponse(
            description='Source subtitle does not belong to this project'
        ),
        404: OpenApiResponse(
            description='Project, content, or source subtitle not found',
        ),
        500: OpenApiResponse(
            description='Internal server error - Translation failed due to API or processing error',
            examples=[
                OpenApiExample(
                    'Translation Failed',
                    value={
                        'error': 'Translation failed: GEMINI_API_KEY not configured in settings',
                    },
                ),
            ],
        ),
    },
    examples=[
        OpenApiExample(
            'Translate to Persian',
            value={
                'source_subtitle_id': 'bb0e8400-e29b-41d4-a716-446655440000',
                'target_language': 'persian',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Translate to Spanish',
            value={
                'source_subtitle_id': 'bb0e8400-e29b-41d4-a716-446655440000',
                'target_language': 'spanish',
            },
            request_only=True,
        ),
    ],
)


subtitle_burn_schema = extend_schema(
    operation_id='burn_subtitle',
    summary='Burn (hardcode) subtitle into video',
    description=(
        'Creates a new video file with subtitles permanently burned into the video using ffmpeg. '
        'The subtitle must be completed before burning. '
        'Returns a task that can be monitored for completion.'
    ),
    tags=['Subtitles'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='subtitle_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the subtitle to burn',
            required=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=SubtitleBurnTaskSerializer,
            description='Burn task created successfully',
        ),
        400: OpenApiResponse(
            description='Bad request - Subtitle or video not ready for burning',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        403: OpenApiResponse(
            description='Subtitle does not belong to this project'
        ),
        404: OpenApiResponse(
            description='Project or subtitle not found',
        ),
    },
)


subtitle_burn_status_schema = extend_schema(
    operation_id='get_burn_task_status',
    summary='Get subtitle burn task status',
    description=(
        'Retrieves the current status of a subtitle burn task. '
        'Returns the output file path when the task is completed.'
    ),
    tags=['Subtitles'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='burn_task_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the burn task',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=SubtitleBurnTaskSerializer,
            description='Burn task status retrieved successfully',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        403: OpenApiResponse(
            description='Burn task does not belong to this project'
        ),
        404: OpenApiResponse(
            description='Project or burn task not found',
        ),
    },
)


# Keep the old subtitle_status_schema for backward compatibility if needed
subtitle_status_schema = extend_schema(
    operation_id='get_subtitle_status',
    summary='Get subtitle generation status and result',
    description=(
        'Retrieves the current status and result of the subtitle generation task for a specific project. '
        'Returns the complete subtitle text when generation is completed. '
        'Only applicable for projects with video content.'
    ),
    tags=['Subtitles'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to check subtitle status for',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=SubtitleSerializer,
            description='Subtitle status retrieved successfully',
            examples=[
                OpenApiExample(
                    'Subtitle Pending',
                    value={
                        'id': 'bb0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'platform': 'youtube',
                        'project_title': 'My Video Project',
                        'task_id': 'celery-task-id-67890',
                        'status': 'pending',
                        'subtitle_text': None,
                        'error_message': None,
                        'started_at': None,
                        'completed_at': None,
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:00:00Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Subtitle Generating',
                    value={
                        'id': 'bb0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'platform': 'youtube',
                        'project_title': 'My Video Project',
                        'task_id': 'celery-task-id-67890',
                        'status': 'generating',
                        'subtitle_text': None,
                        'error_message': None,
                        'started_at': '2024-01-15T12:00:30Z',
                        'completed_at': None,
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:00:30Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Subtitle Completed',
                    value={
                        'id': 'bb0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'platform': 'youtube',
                        'project_title': 'My Video Project',
                        'task_id': 'celery-task-id-67890',
                        'status': 'completed',
                        'subtitle_text': '1\n00:00:00,000 --> 00:00:03,000\nFirst subtitle text here\n\n2\n00:00:03,000 --> 00:00:06,000\nSecond subtitle text here',
                        'error_message': None,
                        'started_at': '2024-01-15T12:00:30Z',
                        'completed_at': '2024-01-15T12:02:15Z',
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:02:15Z',
                    },
                    response_only=True,
                ),
                OpenApiExample(
                    'Subtitle Failed',
                    value={
                        'id': 'bb0e8400-e29b-41d4-a716-446655440000',
                        'content': '990e8400-e29b-41d4-a716-446655440000',
                        'content_url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ',
                        'platform': 'youtube',
                        'project_title': 'My Video Project',
                        'task_id': 'celery-task-id-67890',
                        'status': 'failed',
                        'subtitle_text': None,
                        'error_message': 'GEMINI_API_KEY not configured in settings',
                        'started_at': '2024-01-15T12:00:30Z',
                        'completed_at': '2024-01-15T12:00:35Z',
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:00:35Z',
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
            description='Project, content, or subtitle not found',
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
                OpenApiExample(
                    'Subtitle Not Found',
                    value={
                        'error': 'No subtitle found for this content. Generate subtitles first.',
                    },
                ),
            ],
        ),
    },
)


# WATERMARK ENDPOINTS SCHEMAS
watermark_create_schema = extend_schema(
    operation_id='create_watermark_task',
    summary='Burn watermark into video',
    description=(
        'Uploads a watermark image and burns it into the project\'s video. '
        'The watermark will be positioned at the bottom right corner of the video. '
        'PNG images with transparency are recommended for best results. '
        'Returns a task that can be monitored for completion.'
    ),
    tags=['Watermarks'],
    request=WatermarkCreateSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=WatermarkTaskSerializer,
            description='Watermark task created successfully',
        ),
        400: OpenApiResponse(
            description='Bad request - Video not downloaded or invalid data',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or content not found',
        ),
    },
)


watermark_status_schema = extend_schema(
    operation_id='get_watermark_task_status',
    summary='Get watermark task status',
    description=(
        'Retrieves the current status of a watermark task. '
        'Returns the output file path when the task is completed.'
    ),
    tags=['Watermarks'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='watermark_task_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the watermark task',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=WatermarkTaskSerializer,
            description='Watermark task status retrieved successfully',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        403: OpenApiResponse(
            description='Watermark task does not belong to this project'
        ),
        404: OpenApiResponse(
            description='Project or watermark task not found',
        ),
    },
)

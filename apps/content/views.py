"""
Views for content management APIs.
"""
import logging
from django.shortcuts import get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

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
from apps.content.services import (
    create_content_from_search_result, 
    delete_content, 
    create_subtitle_generation_task,
    translate_subtitle_synchronous,
    create_subtitle_burn_task,
    delete_subtitle,
    create_watermark_task,
)
from apps.content.selectors import (
    get_download_task_by_id, 
    get_project_content, 
    get_subtitle_by_content,
    get_subtitle_by_id,
    list_subtitles_by_content,
    get_burn_task_by_id,
    get_watermark_task_by_id,
)
from apps.search.selectors import get_project_by_id
from apps.search.models import SearchResult
from apps.content.schemas import (
    content_create_schema,
    content_detail_schema,
    video_download_status_schema,
    video_download_task_detail_schema,
    content_delete_schema,
    subtitle_generate_schema,
    subtitle_list_schema,
    subtitle_delete_schema,
    subtitle_translate_schema,
    subtitle_burn_schema,
    subtitle_burn_status_schema,
    watermark_create_schema,
    watermark_status_schema,
)

logger = logging.getLogger(__name__)


class ContentCreateView(APIView):
    """
    POST: Create content from a search result and trigger video download if needed.
    
    Request body:
        - search_result_id: UUID
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = ContentCreateSerializer

    @content_create_schema
    def post(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if hasattr(project, 'content'):
            return Response(
                {"error": "Content already exists for this project."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        search_result_id = serializer.validated_data['search_result_id']
        
        try:
            search_result = SearchResult.objects.select_related('search_request__project').get(
                id=search_result_id
            )

            if search_result.search_request.project_id != project.id:
                return Response(
                    {"error": "Search result does not belong to this project."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except SearchResult.DoesNotExist:
            return Response(
                {"error": "Search result not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = create_content_from_search_result(
            project=project,
            search_result=search_result
        )

        response_serializer = ContentSerializer(content)
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class ContentDetailView(APIView):
    """
    GET: Retrieve content for a project.
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ContentSerializer

    @content_detail_schema
    def get(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        content = get_project_content(project)
        if not content:
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(content)
        return Response(serializer.data, status=status.HTTP_200_OK)


class VideoDownloadStatusView(APIView):
    """
    GET: Get the status of a video download task for a project.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = VideoDownloadTaskSerializer
    
    @video_download_status_schema
    def get(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)        
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if not hasattr(project, 'content'):
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = project.content
        
        if content.content_type != 'video':
            return Response(
                {"error": "Content is not a video."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        download_task = content.download_task
        serializer = self.serializer_class(download_task)
        return Response(serializer.data, status=status.HTTP_200_OK)
        

class VideoDownloadTaskDetailView(APIView):
    """
    GET: Get details of a specific download task by task ID.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = VideoDownloadTaskSerializer
    
    @video_download_task_detail_schema
    def get(self, request, task_id):
        download_task = get_download_task_by_id(task_id)

        if not download_task:
            return Response(
                {"error": "Download task not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        project = download_task.content.project
        if project.owner_id != request.user.id:
            return Response(
                {"error": "Access denied."},
                status=status.HTTP_403_FORBIDDEN,
            )

        serializer = self.serializer_class(download_task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class ContentDeleteView(APIView):
    """
    DELETE: Delete content for a project.
    """
    
    permission_classes = [IsAuthenticated]
    
    @content_delete_schema
    def delete(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = get_project_content(project)
        if not content:
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        delete_content(content)
        
        logger.info(f"User {request.user.id} deleted content for project {project_id}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubtitleGenerateView(APIView):
    """
    POST: Generate subtitles for a project's video content.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SubtitleSerializer
    
    @subtitle_generate_schema
    def post(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = get_project_content(project)
        if not content:
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if content.content_type != 'video':
            return Response(
                {"error": "Content is not a video. Subtitles can only be generated for video content."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Check if original subtitle already exists
        existing_subtitle = get_subtitle_by_content(content, language='original')
        if existing_subtitle and existing_subtitle.status not in ['failed']:
            return Response(
                {"error": "Subtitle already exists for this content. Use the regenerate endpoint if you want to regenerate."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # If exists but failed, delete it and create new one
        if existing_subtitle and existing_subtitle.status == 'failed':
            delete_subtitle(existing_subtitle)
        
        try:
            subtitle = create_subtitle_generation_task(content, language='original')
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = self.serializer_class(subtitle)
        
        logger.info(f"User {request.user.id} initiated subtitle generation for project {project_id}")
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class SubtitleListView(APIView):
    """
    GET: List all subtitles for a project's content.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SubtitleSerializer
    
    @subtitle_list_schema
    def get(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = get_project_content(project)
        if not content:
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if content.content_type != 'video':
            return Response(
                {"error": "Content is not a video."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        subtitles = list_subtitles_by_content(content)
        serializer = self.serializer_class(subtitles, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class SubtitleDeleteView(APIView):
    """
    DELETE: Delete a specific subtitle.
    """
    
    permission_classes = [IsAuthenticated]
    
    @subtitle_delete_schema
    def delete(self, request, project_id, subtitle_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        subtitle = get_subtitle_by_id(subtitle_id)
        if not subtitle:
            return Response(
                {"error": "Subtitle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verify subtitle belongs to this project
        if subtitle.content.project_id != project.id:
            return Response(
                {"error": "Subtitle does not belong to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        delete_subtitle(subtitle)
        
        logger.info(f"User {request.user.id} deleted subtitle {subtitle_id} for project {project_id}")
        
        return Response(status=status.HTTP_204_NO_CONTENT)


class SubtitleTranslateView(APIView):
    """
    POST: Translate a subtitle to a different language using AI (synchronous).
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SubtitleTranslateSerializer
    
    @subtitle_translate_schema
    def post(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = get_project_content(project)
        if not content:
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if content.content_type != 'video':
            return Response(
                {"error": "Content is not a video."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        source_subtitle_id = serializer.validated_data['source_subtitle_id']
        target_language = serializer.validated_data['target_language']
        
        source_subtitle = get_subtitle_by_id(str(source_subtitle_id))
        if not source_subtitle:
            return Response(
                {"error": "Source subtitle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verify source subtitle belongs to this project
        if source_subtitle.content.project_id != project.id:
            return Response(
                {"error": "Source subtitle does not belong to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        try:
            # Perform translation synchronously
            translated_subtitle = translate_subtitle_synchronous(source_subtitle, target_language)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            logger.error(f"Translation failed for project {project_id}: {str(e)}", exc_info=True)
            return Response(
                {"error": f"Translation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        
        response_serializer = SubtitleSerializer(translated_subtitle)
        
        logger.info(f"User {request.user.id} completed subtitle translation to {target_language} for project {project_id}")
        
        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )


class SubtitleBurnView(APIView):
    """
    POST: Start burning (hardcoding) subtitles into video using ffmpeg.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SubtitleBurnTaskSerializer
    
    @subtitle_burn_schema
    def post(self, request, project_id, subtitle_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        subtitle = get_subtitle_by_id(subtitle_id)
        if not subtitle:
            return Response(
                {"error": "Subtitle not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verify subtitle belongs to this project
        if subtitle.content.project_id != project.id:
            return Response(
                {"error": "Subtitle does not belong to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        try:
            burn_task = create_subtitle_burn_task(subtitle)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = self.serializer_class(burn_task)
        
        logger.info(f"User {request.user.id} initiated subtitle burn task for subtitle {subtitle_id}")
        
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )


class SubtitleBurnStatusView(APIView):
    """
    GET: Get the status of a subtitle burn task.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SubtitleBurnTaskSerializer
    
    @subtitle_burn_status_schema
    def get(self, request, project_id, burn_task_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        burn_task = get_burn_task_by_id(burn_task_id)
        if not burn_task:
            return Response(
                {"error": "Burn task not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verify burn task belongs to this project
        if burn_task.subtitle.content.project_id != project.id:
            return Response(
                {"error": "Burn task does not belong to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = self.serializer_class(burn_task)
        return Response(serializer.data, status=status.HTTP_200_OK)


class WatermarkCreateView(APIView):
    """
    POST: Upload watermark image and start burning it into video.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = WatermarkCreateSerializer
    
    @watermark_create_schema
    def post(self, request, project_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        content = get_project_content(project)
        if not content:
            return Response(
                {"error": "No content found for this project."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        if content.content_type != 'video':
            return Response(
                {"error": "Content is not a video. Watermark can only be added to video content."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        watermark_image = serializer.validated_data['watermark_image']
        
        try:
            watermark_task = create_watermark_task(content, watermark_image)
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        response_serializer = WatermarkTaskSerializer(watermark_task, context={'request': request})
        
        logger.info(f"User {request.user.id} initiated watermark burn task for project {project_id}")
        
        return Response(
            response_serializer.data,
            status=status.HTTP_201_CREATED
        )


class WatermarkStatusView(APIView):
    """
    GET: Get the status of a watermark task.
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = WatermarkTaskSerializer
    
    @watermark_status_schema
    def get(self, request, project_id, watermark_task_id):
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        watermark_task = get_watermark_task_by_id(watermark_task_id)
        if not watermark_task:
            return Response(
                {"error": "Watermark task not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Verify watermark task belongs to this project
        if watermark_task.content.project_id != project.id:
            return Response(
                {"error": "Watermark task does not belong to this project."},
                status=status.HTTP_403_FORBIDDEN,
            )
        
        serializer = self.serializer_class(watermark_task, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

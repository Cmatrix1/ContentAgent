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
)
from apps.content.services import create_content_from_search_result
from apps.content.selectors import get_download_task_by_id
from apps.search.selectors import get_project_by_id
from apps.search.models import SearchResult
from apps.content.schemas import (
    content_create_schema,
    video_download_status_schema,
    video_download_task_detail_schema,
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

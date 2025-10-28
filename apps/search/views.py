from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.search.serializers import (
    ProjectSerializer,
    SearchRequestSerializer,
    SearchResultSerializer,
)
from apps.search.services import (
    create_project,
    create_search_request,
)
from apps.search.selectors import (
    get_project_by_id,
    list_search_results_for_project,
)
from apps.search.schemas import (
    project_create_schema,
    search_request_create_schema,
    search_result_list_schema,
)


class ProjectCreateView(APIView):
    """
    POST: Create a new project for the authenticated user
    """

    permission_classes = [IsAuthenticated]
    serializer_class = ProjectSerializer
    
    @project_create_schema
    def post(self, request):
        """Create a new project for the authenticated user."""
        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            project = create_project(
                owner_id=request.user.id,
                title=serializer.validated_data["title"],
                type=serializer.validated_data.get("type", "text"),
            )
            response_serializer = self.serializer_class(project)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchRequestCreateView(APIView):
    """
    POST: Create a new search request for a specific project
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SearchRequestSerializer
    
    @search_request_create_schema
    def post(self, request, project_id):
        """Create a search request for the given project."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = self.serializer_class(data=request.data)
        if serializer.is_valid():
            search_request = create_search_request(
                project=project,
                query=serializer.validated_data["query"],
                language=serializer.validated_data.get("language", "en"),
                top_results_count=serializer.validated_data.get("top_results_count", 10),
                params=serializer.validated_data.get("params"),
            )
            response_serializer = self.serializer_class(search_request)
            return Response(response_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class SearchResultListView(APIView):
    """
    GET: List all search results for a specific project
    Query params:
        - only_selected: boolean to filter only selected results
    """

    permission_classes = [IsAuthenticated]
    serializer_class = SearchResultSerializer
    
    @search_result_list_schema
    def get(self, request, project_id):
        """List search results for the given project."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )

        only_selected = (
            request.query_params.get("only_selected", "false").lower() == "true"
        )

        search_results = list_search_results_for_project(
            project=project,
            only_selected=only_selected,
        )

        serializer = self.serializer_class(search_results, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


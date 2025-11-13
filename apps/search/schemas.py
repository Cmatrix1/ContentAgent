"""
OpenAPI schema documentation for Search app views.
Contains request/response examples and detailed documentation for all endpoints.
"""
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.types import OpenApiTypes
from apps.search.serializers import (
    ProjectSerializer,
    SearchRequestSerializer,
    SearchResultSerializer,
)


project_list_schema = extend_schema(
    operation_id='list_projects',
    summary='List projects for the authenticated user',
    description='Retrieves all projects owned by the authenticated user.',
    tags=['Projects'],
    responses={
        200: OpenApiResponse(
            response=ProjectSerializer(many=True),
            description='Projects retrieved successfully',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
    },
)


project_create_schema = extend_schema(
    operation_id='create_project',
    summary='Create a new project',
    description=(
        'Creates a new project for the authenticated user. '
        'A project is the main container for organizing search requests and content.'
    ),
    tags=['Projects'],
    request=ProjectSerializer,
    responses={
        201: OpenApiResponse(
            response=ProjectSerializer,
            description='Project created successfully',
            examples=[
                OpenApiExample(
                    'Project Created',
                    value={
                        'id': '550e8400-e29b-41d4-a716-446655440000',
                        'owner': 1,
                        'title': 'My Content Project',
                        'type': 'video',
                        'status': 'draft',
                        'created_at': '2024-01-15T10:30:00Z',
                        'updated_at': '2024-01-15T10:30:00Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data provided',
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={
                        'title': ['This field is required.'],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
    },
    examples=[
        OpenApiExample(
            'Video Project',
            value={
                'title': 'My Video Content Project',
                'type': 'video',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Text Project',
            value={
                'title': 'Blog Post Research',
                'type': 'text',
            },
            request_only=True,
        ),
    ],
)


project_delete_schema = extend_schema(
    operation_id='delete_project',
    summary='Delete a project',
    description='Delete a project owned by the authenticated user.',
    tags=['Projects'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to delete',
            required=True,
        ),
    ],
    responses={
        204: OpenApiResponse(
            description='Project deleted successfully',
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project not found or access denied',
            examples=[
                OpenApiExample(
                    'Project Not Found',
                    value={
                        'error': 'Project not found or access denied.',
                    },
                ),
            ],
        ),
    },
)


search_request_create_schema = extend_schema(
    operation_id='create_search_request',
    summary='Create a search request for a project',
    description=(
        'Creates a new search request for a specific project. '
        'This will trigger a Google Custom Search to find relevant content. '
        'The search results will be automatically fetched and stored.'
    ),
    tags=['Search'],
    request=SearchRequestSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to create search request for',
            required=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=SearchRequestSerializer,
            description='Search request created successfully',
            examples=[
                OpenApiExample(
                    'Search Request Created',
                    value={
                        'id': '660e8400-e29b-41d4-a716-446655440000',
                        'project': '550e8400-e29b-41d4-a716-446655440000',
                        'query': 'best practices for Django REST API',
                        'language': 'en',
                        'top_results_count': 10,
                        'params': {},
                        'status': 'pending',
                        'created_at': '2024-01-15T10:35:00Z',
                        'completed_at': None,
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data or project already has content',
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={
                        'query': ['This field is required.'],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project not found or access denied',
            examples=[
                OpenApiExample(
                    'Project Not Found',
                    value={
                        'error': 'Project not found or access denied.',
                    },
                ),
            ],
        ),
    },
    examples=[
        OpenApiExample(
            'Basic Search',
            value={
                'query': 'Python Django tutorials',
                'language': 'en',
                'top_results_count': 10,
            },
            request_only=True,
        ),
        OpenApiExample(
            'Advanced Search with Parameters',
            value={
                'query': 'React hooks explained',
                'language': 'en',
                'top_results_count': 20,
                'params': {
                    'dateRestrict': 'm6',  # Last 6 months
                    'siteSearch': 'medium.com',
                },
            },
            request_only=True,
        ),
    ],
)


search_result_list_schema = extend_schema(
    operation_id='list_search_results',
    summary='List search results for a project',
    description=(
        'Retrieves all search results for a specific project. '
        'Results can be filtered to show only selected items using the query parameter.'
    ),
    tags=['Search'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to retrieve search results for',
            required=True,
        ),
        OpenApiParameter(
            name='only_selected',
            type=OpenApiTypes.BOOL,
            location=OpenApiParameter.QUERY,
            description='Filter to show only selected results (default: false)',
            required=False,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=SearchResultSerializer(many=True),
            description='Search results retrieved successfully',
            examples=[
                OpenApiExample(
                    'Search Results List',
                    value=[
                        {
                            'id': '770e8400-e29b-41d4-a716-446655440000',
                            'search_request': '660e8400-e29b-41d4-a716-446655440000',
                            'title': 'Django REST Framework - Best Practices',
                            'link': 'https://example.com/django-best-practices',
                            'snippet': 'Comprehensive guide to Django REST Framework best practices...',
                            'rank': 1,
                            'is_selected': True,
                            'metadata': {
                                'pagemap': {
                                    'metatags': [
                                        {
                                            'og:title': 'Django REST Framework Guide',
                                        }
                                    ]
                                }
                            },
                            'fetched_at': '2024-01-15T10:36:00Z',
                        },
                        {
                            'id': '880e8400-e29b-41d4-a716-446655440000',
                            'search_request': '660e8400-e29b-41d4-a716-446655440000',
                            'title': 'Building RESTful APIs with Django',
                            'link': 'https://example.com/restful-apis-django',
                            'snippet': 'Learn how to build scalable RESTful APIs using Django...',
                            'rank': 2,
                            'is_selected': False,
                            'metadata': {},
                            'fetched_at': '2024-01-15T10:36:00Z',
                        },
                    ],
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project not found or access denied',
            examples=[
                OpenApiExample(
                    'Project Not Found',
                    value={
                        'error': 'Project not found or access denied.',
                    },
                ),
            ],
        ),
    },
)


"""
OpenAPI schema documentation for Copywriting app views.
Contains request/response examples and detailed documentation for all endpoints.
"""
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
)
from drf_spectacular.types import OpenApiTypes
from apps.copywriting.serializers import (
    CopywritingSessionSerializer,
    GenerateCopywritingSerializer,
    EditSectionSerializer,
    RegenerateSectionSerializer,
)



copywriting_generate_schema = extend_schema(
    operation_id='generate_copywriting',
    summary='Generate AI copywriting for a project',
    description=(
        'Generates marketing texts (title, caption, meta description, hashtags, etc.) '
        'for a project using AI. The system collects data from the project and uses '
        'LangChain with LLM to generate engaging copy in Persian.'
    ),
    tags=['Copywriting'],
    request=GenerateCopywritingSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project to generate copywriting for',
            required=True,
        ),
    ],
    responses={
        201: OpenApiResponse(
            response=CopywritingSessionSerializer,
            description='Copywriting generated successfully',
            examples=[
                OpenApiExample(
                    'Copywriting Generated',
                    value={
                        'id': 'cc0e8400-e29b-41d4-a716-446655440000',
                        'project': '550e8400-e29b-41d4-a716-446655440000',
                        'inputs': {
                            'title': 'My Content Project',
                            'description': 'Project description',
                            'platform': 'instagram',
                            'user_description': 'Make it engaging',
                        },
                        'outputs': {
                            'title': 'عنوان جذاب برای پروژه',
                            'caption': 'متن تبلیغاتی کامل...',
                            'micro_caption': 'متن کوتاه',
                            'meta_description': 'توضیحات متا',
                            'hashtags': ['#تگ1', '#تگ2'],
                            'cta': 'همین حالا ببینید',
                            'alt_text': 'متن جایگزین',
                        },
                        'edits': {},
                        'final_outputs': {
                            'title': 'عنوان جذاب برای پروژه',
                            'caption': 'متن تبلیغاتی کامل...',
                            'micro_caption': 'متن کوتاه',
                            'meta_description': 'توضیحات متا',
                            'hashtags': ['#تگ1', '#تگ2'],
                            'cta': 'همین حالا ببینید',
                            'alt_text': 'متن جایگزین',
                        },
                        'status': 'pending',
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:00:00Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data',
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={
                        'description': ['Ensure this field has no more than 1000 characters.'],
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
            'Generate with Description',
            value={
                'description': 'Make it engaging and SEO-friendly',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Generate without Description',
            value={},
            request_only=True,
        ),
    ],
)



copywriting_session_detail_schema = extend_schema(
    operation_id='get_copywriting_session',
    summary='Get copywriting session details',
    description=(
        'Retrieves all data for a specific copywriting session including inputs, '
        'AI-generated outputs, user edits, and the final merged outputs.'
    ),
    tags=['Copywriting'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the copywriting session',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=CopywritingSessionSerializer,
            description='Session details retrieved successfully',
            examples=[
                OpenApiExample(
                    'Session Details',
                    value={
                        'id': 'cc0e8400-e29b-41d4-a716-446655440000',
                        'project': '550e8400-e29b-41d4-a716-446655440000',
                        'inputs': {
                            'title': 'My Content Project',
                            'description': 'Project description',
                            'platform': 'instagram',
                        },
                        'outputs': {
                            'title': 'عنوان اصلی',
                            'caption': 'متن اصلی',
                            'cta': 'CTA اصلی',
                        },
                        'edits': {
                            'cta': 'CTA ویرایش شده',
                        },
                        'final_outputs': {
                            'title': 'عنوان اصلی',
                            'caption': 'متن اصلی',
                            'cta': 'CTA ویرایش شده',
                        },
                        'status': 'pending',
                        'created_at': '2024-01-15T12:00:00Z',
                        'updated_at': '2024-01-15T12:05:00Z',
                    },
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or session not found',
            examples=[
                OpenApiExample(
                    'Session Not Found',
                    value={
                        'error': 'Copywriting session not found.',
                    },
                ),
            ],
        ),
    },
)


# COPYWRITING EDIT SECTION SCHEMA

copywriting_edit_section_schema = extend_schema(
    operation_id='edit_copywriting_section',
    summary='Edit a section of copywriting',
    description=(
        'Manually edit a specific section of the copywriting. '
        'The edit is stored separately and will override the AI-generated value '
        'in the final outputs.'
    ),
    tags=['Copywriting'],
    request=EditSectionSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the copywriting session',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Section edited successfully',
            examples=[
                OpenApiExample(
                    'Edit Success',
                    value={
                        'message': 'Section "cta" updated successfully.',
                        'section': 'cta',
                        'new_value': 'همین الان کلیک کنید!',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data',
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={
                        'section': ['This field is required.'],
                        'new_value': ['This field is required.'],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or session not found',
        ),
    },
    examples=[
        OpenApiExample(
            'Edit CTA',
            value={
                'section': 'cta',
                'new_value': 'همین الان کلیک کنید!',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Edit Caption',
            value={
                'section': 'caption',
                'new_value': 'متن جدید برای کپشن که توسط کاربر ویرایش شده است.',
            },
            request_only=True,
        ),
    ],
)


# COPYWRITING REGENERATE SECTION SCHEMA

copywriting_regenerate_section_schema = extend_schema(
    operation_id='regenerate_copywriting_section',
    summary='Regenerate a section using AI',
    description=(
        'Regenerate a specific section of copywriting using AI with custom instructions. '
        'The AI will consider the current value, project context, and your instructions '
        'to generate a new version of the section.'
    ),
    tags=['Copywriting'],
    request=RegenerateSectionSerializer,
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the copywriting session',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Section regenerated successfully',
            examples=[
                OpenApiExample(
                    'Regenerate Success',
                    value={
                        'message': 'Section "caption" regenerated successfully.',
                        'section': 'caption',
                        'new_value': 'متن جدید که کوتاه‌تر و خنده‌دارتر است.',
                    },
                    response_only=True,
                ),
            ],
        ),
        400: OpenApiResponse(
            description='Bad request - Invalid data',
            examples=[
                OpenApiExample(
                    'Validation Error',
                    value={
                        'section': ['This field is required.'],
                        'instruction': ['This field is required.'],
                    },
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or session not found',
        ),
    },
    examples=[
        OpenApiExample(
            'Make Caption Shorter',
            value={
                'section': 'caption',
                'instruction': 'Make it shorter and funnier',
            },
            request_only=True,
        ),
        OpenApiExample(
            'Improve CTA',
            value={
                'section': 'cta',
                'instruction': 'Make it more urgent and action-oriented',
            },
            request_only=True,
        ),
    ],
)


# COPYWRITING SAVE FINAL SCHEMA

copywriting_save_final_schema = extend_schema(
    operation_id='save_final_copywriting',
    summary='Save final copywriting outputs',
    description=(
        'Mark the session as completed and return the final merged outputs. '
        'This merges the AI-generated outputs with any manual edits, with edits '
        'taking precedence.'
    ),
    tags=['Copywriting'],
    parameters=[
        OpenApiParameter(
            name='project_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the project',
            required=True,
        ),
        OpenApiParameter(
            name='session_id',
            type=OpenApiTypes.UUID,
            location=OpenApiParameter.PATH,
            description='UUID of the copywriting session',
            required=True,
        ),
    ],
    responses={
        200: OpenApiResponse(
            description='Final outputs saved successfully',
            examples=[
                OpenApiExample(
                    'Save Success',
                    value={
                        'message': 'Copywriting saved successfully.',
                        'status': 'completed',
                        'final_outputs': {
                            'title': 'عنوان نهایی',
                            'caption': 'متن نهایی',
                            'micro_caption': 'متن کوتاه',
                            'meta_description': 'توضیحات متا',
                            'hashtags': ['#تگ1', '#تگ2', '#تگ3'],
                            'cta': 'CTA ویرایش شده',
                            'alt_text': 'متن جایگزین',
                        },
                    },
                    response_only=True,
                ),
            ],
        ),
        401: OpenApiResponse(
            description='Authentication credentials were not provided or are invalid'
        ),
        404: OpenApiResponse(
            description='Project or session not found',
        ),
    },
)


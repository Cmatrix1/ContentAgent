import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated

from apps.copywriting.serializers import (
    CopywritingSessionSerializer,
    GenerateCopywritingSerializer,
    EditSectionSerializer,
    RegenerateSectionSerializer,
    SaveFinalSerializer,
)
from apps.copywriting.services import (
    create_copywriting_session,
    update_session_edit,
    regenerate_session_section,
    finalize_session,
)
from apps.copywriting.selectors import get_copywriting_session_by_id
from apps.copywriting.schemas import (
    copywriting_generate_schema,
    copywriting_session_detail_schema,
    copywriting_edit_section_schema,
    copywriting_regenerate_section_schema,
    copywriting_save_final_schema,
)
from apps.search.selectors import get_project_by_id

logger = logging.getLogger(__name__)


class CopywritingGenerateView(APIView):
    """
    POST: Generate AI copywriting for a project
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = GenerateCopywritingSerializer
    
    @copywriting_generate_schema
    def post(self, request, project_id):
        """Generate copywriting for the given project."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        user_description = serializer.validated_data.get('description', '')        
        session = create_copywriting_session(
            project=project,
            user_description=user_description,
        )
        response_serializer = CopywritingSessionSerializer(session)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)



class CopywritingSessionDetailView(APIView):
    """
    GET: Get details of a copywriting session
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = CopywritingSessionSerializer
    
    @copywriting_session_detail_schema
    def get(self, request, project_id, session_id):
        """Get copywriting session details."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        session = get_copywriting_session_by_id(project=project, session_id=session_id)
        if not session:
            return Response(
                {"error": "Copywriting session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = self.serializer_class(session)
        return Response(serializer.data, status=status.HTTP_200_OK)


class CopywritingEditSectionView(APIView):
    """
    PATCH: Edit a section of copywriting manually
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = EditSectionSerializer
    
    @copywriting_edit_section_schema
    def patch(self, request, project_id, session_id):
        """Edit a section of the copywriting."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        session = get_copywriting_session_by_id(project=project, session_id=session_id)
        if not session:
            return Response(
                {"error": "Copywriting session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        section = serializer.validated_data['section']
        new_value = serializer.validated_data['new_value']
        
        update_session_edit(
            session=session,
            section=section,
            new_value=new_value,
        )
        return Response(
            {
                "message": f'Section "{section}" updated successfully.',
                "section": section,
                "new_value": new_value,
            },
            status=status.HTTP_200_OK,
        )



class CopywritingRegenerateSectionView(APIView):
    """
    POST: Regenerate a section using AI with custom instructions
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = RegenerateSectionSerializer
    
    @copywriting_regenerate_section_schema
    def post(self, request, project_id, session_id):
        """Regenerate a section of the copywriting."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        session = get_copywriting_session_by_id(project=project, session_id=session_id)
        if not session:
            return Response(
                {"error": "Copywriting session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = self.serializer_class(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        section = serializer.validated_data['section']
        instruction = serializer.validated_data['instruction']
        
        _, new_value = regenerate_session_section(
            session=session,
            section=section,
            instruction=instruction,
        )
        return Response(
            {
                "message": f'Section "{section}" regenerated successfully.',
                "section": section,
                "new_value": new_value,
            },
            status=status.HTTP_200_OK,
        )



class CopywritingSaveFinalView(APIView):
    """
    POST: Save final copywriting outputs and mark as completed
    """
    
    permission_classes = [IsAuthenticated]
    serializer_class = SaveFinalSerializer
    
    @copywriting_save_final_schema
    def post(self, request, project_id, session_id):
        """Save final copywriting outputs."""
        project = get_project_by_id(owner_id=request.user.id, project_id=project_id)
        if not project:
            return Response(
                {"error": "Project not found or access denied."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        session = get_copywriting_session_by_id(project=project, session_id=session_id)
        if not session:
            return Response(
                {"error": "Copywriting session not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        final_outputs = finalize_session(session=session)
        return Response(
            {
                "message": "Copywriting saved successfully.",
                "status": "completed",
                "final_outputs": final_outputs,
            },
            status=status.HTTP_200_OK,
        )

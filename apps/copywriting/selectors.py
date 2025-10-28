from typing import Optional
from uuid import UUID

from django.db.models import QuerySet

from apps.copywriting.models import CopywritingSession
from apps.search.models import Project


def list_copywriting_sessions_for_project(project: Project) -> QuerySet[CopywritingSession]:
    """
    List all copywriting sessions for a project.
    
    Args:
        project: The project to list sessions for
    
    Returns:
        QuerySet of CopywritingSession instances
    """
    return CopywritingSession.objects.select_related('project').filter(project=project)


def get_copywriting_session_by_id(
    project: Project, 
    session_id: UUID
) -> Optional[CopywritingSession]:
    """
    Fetch a copywriting session by ID for a specific project.
    
    Args:
        project: The project that owns the session
        session_id: UUID of the session
    
    Returns:
        CopywritingSession instance or None if not found
    """
    return (
        CopywritingSession.objects.select_related('project')
        .filter(id=session_id, project=project)
        .first()
    )


def get_latest_copywriting_session_for_project(project: Project) -> Optional[CopywritingSession]:
    """
    Get the most recent copywriting session for a project.
    
    Args:
        project: The project to get the latest session for
    
    Returns:
        CopywritingSession instance or None if not found
    """
    return (
        CopywritingSession.objects.select_related('project')
        .filter(project=project)
        .order_by('-created_at')
        .first()
    )


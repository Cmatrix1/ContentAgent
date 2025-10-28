"""
Business logic services for copywriting operations.
"""
import logging
from typing import Optional

from django.db import transaction

from apps.copywriting.models import CopywritingSession
from apps.copywriting.services.ai_client import generate_copywriting, regenerate_section
from apps.search.models import Project
from apps.search.selectors import list_search_results_for_project

logger = logging.getLogger(__name__)


@transaction.atomic
def create_copywriting_session(
    *,
    project: Project,
    user_description: Optional[str] = None
) -> CopywritingSession:
    """
    Create a new copywriting session and generate content using AI.
    
    Args:
        project: The project to generate copywriting for
        user_description: Optional user note or description
    
    Returns:
        Created CopywritingSession instance with generated outputs
    """
    # Gather inputs from project
    inputs = {
        'title': project.title,
        'description': getattr(project, 'description', ''),
        'platform': 'other',  # Default platform
        'user_description': user_description or '',
    }
    
    # Try to get platform from content if exists
    if hasattr(project, 'content'):
        content = project.content
        inputs['platform'] = content.platform
        inputs['source_url'] = content.source_url
        inputs['content_type'] = content.content_type
    
    selected_results = list_search_results_for_project(project, only_selected=True)
    search_results_data = []
    for result in selected_results:
        search_results_data.append({
            'title': result.title,
            'snippet': result.snippet,
            'link': result.link,
        })
    
    logger.info(f"Found {len(search_results_data)} selected search results for project {project.id}")
    
    outputs = generate_copywriting(inputs, search_results=search_results_data if search_results_data else None)
    
    session = CopywritingSession.objects.create(
        project=project,
        inputs=inputs,
        outputs=outputs,
        status='pending',
    )
    
    logger.info(f"Created copywriting session {session.id} for project {project.id}")
    
    return session


@transaction.atomic
def update_session_edit(
    *,
    session: CopywritingSession,
    section: str,
    new_value: str
) -> CopywritingSession:
    """
    Update a specific section of the copywriting with user edit.
    
    Args:
        session: The copywriting session to update
        section: Section name to edit
        new_value: New value for the section
    
    Returns:
        Updated CopywritingSession instance
    """
    # Update edits field
    edits = session.edits.copy()
    edits[section] = new_value
    session.edits = edits
    session.save(update_fields=['edits', 'updated_at'])
    
    logger.info(f"Updated session {session.id} section '{section}' with manual edit")
    
    return session


@transaction.atomic
def regenerate_session_section(
    *,
    session: CopywritingSession,
    section: str,
    instruction: str
) -> tuple[CopywritingSession, str]:
    """
    Regenerate a specific section using AI.
    
    Args:
        session: The copywriting session to update
        section: Section name to regenerate
        instruction: User instruction for regeneration
    
    Returns:
        Tuple of (updated session, new section value)
    """
    # Get current value (from edits if exists, otherwise from outputs)
    final_outputs = session.get_final_outputs()
    old_value = final_outputs.get(section, '')
    
    # Prepare context for regeneration
    context = {
        'title': session.inputs.get('title', ''),
        'description': session.inputs.get('description', ''),
        'old_value': old_value,
    }
    
    # Regenerate section using AI
    new_value = regenerate_section(
        context=context,
        section=section,
        instruction=instruction,
    )
    
    # Update outputs field (not edits)
    outputs = session.outputs.copy()
    outputs[section] = new_value
    session.outputs = outputs
    session.save(update_fields=['outputs', 'updated_at'])
    
    logger.info(f"Regenerated session {session.id} section '{section}'")
    
    return session, new_value


@transaction.atomic
def finalize_session(*, session: CopywritingSession) -> dict:
    """
    Mark session as completed and return final merged outputs.
    
    Args:
        session: The copywriting session to finalize
    
    Returns:
        Dictionary with final outputs (outputs + edits merged)
    """
    # Get merged outputs
    final_outputs = session.get_final_outputs()
    
    # Mark session as completed
    session.status = 'completed'
    session.save(update_fields=['status', 'updated_at'])
    
    logger.info(f"Finalized session {session.id}")
    
    return final_outputs


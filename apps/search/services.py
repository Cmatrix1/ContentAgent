from typing import Any, Mapping, Optional

from django.db import transaction
from django.utils import timezone

from apps.search.models import (
    Project,
    SearchRequest,
    SearchResult,
)
from apps.search.google_search import search_google, GoogleSearchError


@transaction.atomic
def create_project(
    *, 
    owner_id: int, 
    title: str, 
    type: str = "text"
) -> Project:
    """Create a new project for the given owner.

    Parameters
    - owner_id: ID of the user that will own the project
    - title: project title
    - type: content type (video or text, default: "text")
    """
    project = Project.objects.create(
        owner_id=owner_id, 
        title=title, 
        type=type
    )
    return project


@transaction.atomic
def create_search_request(
    *, 
    project: Project, 
    query: str, 
    language: str = "en",
    top_results_count: int = 10,
    params: Optional[Mapping[str, Any]] = None,
    auto_search: bool = True
) -> SearchRequest:
    """Create a search request and automatically trigger Google search.

    Parameters
    - project: The project to create the search request for
    - query: The search query string
    - language: Content language (default: "en")
    - top_results_count: Number of top results to fetch (default: 10)
    - params: Additional parameters stored as JSON
    - auto_search: Whether to automatically trigger search (default: True)
    """
    search_request = SearchRequest.objects.create(
        project=project,
        query=query,
        language=language,
        top_results_count=top_results_count,
        params=dict(params or {}),
        status="pending",
    )
    
    if auto_search:
        try:
            perform_google_search(search_request=search_request)
        except GoogleSearchError as e:
            print(f"Search failed for request {search_request.id}: {str(e)}")
            search_request.status = "failed"
            search_request.save(update_fields=["status"])
    
    return search_request



@transaction.atomic
def perform_google_search(*, search_request: SearchRequest) -> SearchRequest:
    """Perform a Google search for a search request and save results to the database.
    
    This function:
    1. Updates the SearchRequest status to in_progress
    2. Performs a Google Custom Search based on project type and request parameters
    3. Saves all search results to the database
    
    Parameters
    - search_request: The SearchRequest to perform the search for
    
    Returns:
        The updated SearchRequest with related SearchResult objects
    """
    project = search_request.project
    
    try:
        search_request.status = "in_progress"
        search_request.save(update_fields=["status"])
        Project.objects.filter(id=project.id).update(status="searching")
        
        search_results = search_google(
            query=search_request.query,
            content_type=project.type,
            num_results=search_request.top_results_count,
        )
        
        result_objects = []
        for result_data in search_results:
            search_result = SearchResult(
                search_request=search_request,
                title=result_data["title"],
                link=result_data["link"],
                snippet=result_data["snippet"],
                rank=result_data["rank"],
                metadata=result_data["metadata"],
            )
            result_objects.append(search_result)
        
        SearchResult.objects.bulk_create(result_objects)
        
        search_request.status = "completed"
        search_request.completed_at = timezone.now()
        search_request.save(update_fields=["status", "completed_at"])
        
        Project.objects.filter(id=project.id).update(status="selecting")
        
        return search_request
        
    except GoogleSearchError as e:
        search_request.status = "failed"
        search_request.completed_at = timezone.now()
        search_request.save(update_fields=["status", "completed_at"])

        Project.objects.filter(id=project.id).update(status="failed")
        
        raise e



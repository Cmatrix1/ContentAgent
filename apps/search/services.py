from typing import Any, Iterable, Mapping, Optional
from urllib.parse import urlparse

from django.db import transaction
from django.utils import timezone

from apps.search.constants import SUPPORTED_PLATFORMS, get_default_platforms
from apps.search.models import Project, SearchRequest, SearchResult
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
def delete_project(*, project: Project) -> None:
    """Delete a project and cascade to related objects."""

    project.delete()


@transaction.atomic
def create_search_request(
    *, 
    project: Project, 
    query: str, 
    language: str = "en",
    top_results_count: int = 10,
    params: Optional[Mapping[str, Any]] = None,
    platforms: Optional[Iterable[str]] = None,
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
    selected_platforms = list(platforms) if platforms is not None else get_default_platforms()

    search_request = SearchRequest.objects.create(
        project=project,
        query=query,
        language=language,
        top_results_count=top_results_count,
        params=dict(params or {}),
        platforms=selected_platforms,
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
            platforms=search_request.platforms,
        )

        filtered_results = _filter_results_by_platforms(
            search_results,
            search_request.platforms,
        )
        
        result_objects = []
        for idx, result_data in enumerate(filtered_results, start=1):
            search_result = SearchResult(
                search_request=search_request,
                title=result_data["title"],
                link=result_data["link"],
                snippet=result_data["snippet"],
                rank=idx,
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


def _filter_results_by_platforms(
    results: list[dict[str, Any]],
    platforms: Optional[Iterable[str]],
) -> list[dict[str, Any]]:
    if not results:
        return []

    selected_platforms = set(platforms or SUPPORTED_PLATFORMS)
    allowed_results: list[dict[str, Any]] = []

    for result in results:
        link = result.get("link", "")
        if not link:
            continue

        parsed = urlparse(link)
        domain = parsed.netloc.lower()
        path = parsed.path.lower()

        if "youtube" in selected_platforms and (
            "youtube.com" in domain or "youtu.be" in domain
        ):
            allowed_results.append(result)
            continue

        if "linkedin" in selected_platforms and "linkedin.com" in domain:
            allowed_results.append(result)
            continue

        if "instagram" in selected_platforms and "instagram.com" in domain:
            if path.startswith("/reel"):
                allowed_results.append(result)

    return allowed_results



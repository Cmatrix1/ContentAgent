from typing import List, Optional, Sequence, Tuple
from uuid import UUID

from django.db.models import QuerySet

from apps.search.models import (
    Project,
    SearchRequest,
    SearchResult,
)


def list_projects_for_owner(owner_id: int) -> QuerySet[Project]:
    """Return projects owned by the given user ordered by recency.

    Uses only owner_id to avoid importing the User model here.
    """

    return Project.objects.filter(owner_id=owner_id).order_by("-created_at")


def get_project_by_id(owner_id: int, project_id: UUID) -> Optional[Project]:
    """Fetch a project by id for a specific owner.

    Returns None when not found or not owned by the user.
    """

    return (
        Project.objects.select_related("owner")
        .filter(id=project_id, owner_id=owner_id)
        .first()
    )


def get_search_request_by_id(project: Project, search_request_id: UUID) -> Optional[SearchRequest]:
    """Fetch a search request belonging to the provided project."""

    return (
        SearchRequest.objects.select_related("project")
        .filter(id=search_request_id, project=project)
        .first()
    )


def list_search_requests_for_project(project: Project) -> QuerySet[SearchRequest]:
    """List all search requests for a project."""

    return SearchRequest.objects.select_related("project").filter(project=project)


def list_search_results_for_project(
    project: Project, *, only_selected: bool = False
) -> QuerySet[SearchResult]:
    """List search results for a project, optionally only those flagged selected.

    Optimized with select_related to avoid N+1 on project access through the
    search_request relation.
    """

    qs = SearchResult.objects.select_related(
        "search_request",
        "search_request__project",
    ).filter(search_request__project=project)

    if only_selected:
        qs = qs.filter(is_selected=True)

    return qs


def get_search_results_by_ids_for_project(
    project: Project, search_result_ids: Sequence[UUID]
) -> QuerySet[SearchResult]:
    """Return search results by IDs that belong to the given project."""

    if not search_result_ids:
        return SearchResult.objects.none()

    return (
        list_search_results_for_project(project)
        .filter(id__in=search_result_ids)
        .order_by("rank")
    )


def list_available_source_choices(project: Project) -> List[Tuple[str, str]]:
    """Return choices (id, title) for selected search results in a project.

    Intended for populating form choices for `selected_source_ids`.
    """

    results = list_search_results_for_project(project, only_selected=True)
    return [(str(result.id), result.title) for result in results]


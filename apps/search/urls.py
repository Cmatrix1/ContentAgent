from django.urls import path
from apps.search.views import (
    ProjectDeleteView,
    ProjectListCreateView,
    SearchRequestCreateView,
    SearchResultListView,
)

urlpatterns = [
    path("projects/", ProjectListCreateView.as_view(), name="project-list-create"),
    path(
        "projects/<uuid:project_id>/",
        ProjectDeleteView.as_view(),
        name="project-delete",
    ),
    path(
        "projects/<uuid:project_id>/search-requests/",
        SearchRequestCreateView.as_view(),
        name="search-request-create",
    ),
    path(
        "projects/<uuid:project_id>/search-results/",
        SearchResultListView.as_view(),
        name="search-result-list",
    ),
]

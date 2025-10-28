from django.urls import path
from apps.copywriting.views import (
    CopywritingGenerateView,
    CopywritingSessionDetailView,
    CopywritingEditSectionView,
    CopywritingRegenerateSectionView,
    CopywritingSaveFinalView,
)

urlpatterns = [
    path(
        "projects/<uuid:project_id>/copywriting/generate/",
        CopywritingGenerateView.as_view(),
        name="copywriting-generate",
    ),
    path(
        "projects/<uuid:project_id>/copywriting/<uuid:session_id>/",
        CopywritingSessionDetailView.as_view(),
        name="copywriting-session-detail",
    ),
    path(
        "projects/<uuid:project_id>/copywriting/<uuid:session_id>/edit/",
        CopywritingEditSectionView.as_view(),
        name="copywriting-edit-section",
    ),
    path(
        "projects/<uuid:project_id>/copywriting/<uuid:session_id>/regenerate/",
        CopywritingRegenerateSectionView.as_view(),
        name="copywriting-regenerate-section",
    ),
    path(
        "projects/<uuid:project_id>/copywriting/<uuid:session_id>/save/",
        CopywritingSaveFinalView.as_view(),
        name="copywriting-save-final",
    ),
]


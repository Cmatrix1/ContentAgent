from rest_framework import serializers
from apps.search.models import Project, SearchRequest, SearchResult
from apps.search.constants import SUPPORTED_PLATFORMS, get_default_platforms


class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = [
            "id",
            "owner",
            "title",
            "type",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "owner", "status", "created_at", "updated_at"]


class SearchRequestSerializer(serializers.ModelSerializer):
    platforms = serializers.ListField(
        child=serializers.ChoiceField(choices=SUPPORTED_PLATFORMS),
        allow_empty=False,
        required=False,
        default=get_default_platforms,
    )

    class Meta:
        model = SearchRequest
        fields = [
            "id",
            "project",
            "query",
            "language",
            "top_results_count",
            "params",
            "platforms",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["id", "project", "status", "created_at", "completed_at"]

    def validate_platforms(self, value):
        if not value:
            return SUPPORTED_PLATFORMS.copy()
        # remove duplicates while preserving order
        seen = set()
        unique_platforms = []
        for platform in value:
            if platform not in seen:
                seen.add(platform)
                unique_platforms.append(platform)
        return unique_platforms


class SearchResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = SearchResult
        fields = [
            "id",
            "search_request",
            "title",
            "link",
            "snippet",
            "rank",
            "is_selected",
            "metadata",
            "fetched_at",
        ]
        read_only_fields = [
            "id",
            "search_request",
            "title",
            "link",
            "snippet",
            "rank",
            "metadata",
            "fetched_at",
        ]



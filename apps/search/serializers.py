from rest_framework import serializers
from apps.search.models import Project, SearchRequest, SearchResult


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
    class Meta:
        model = SearchRequest
        fields = [
            "id",
            "project",
            "query",
            "language",
            "top_results_count",
            "params",
            "status",
            "created_at",
            "completed_at",
        ]
        read_only_fields = ["id", "project", "status", "created_at", "completed_at"]


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



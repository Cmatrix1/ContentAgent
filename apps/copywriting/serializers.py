from rest_framework import serializers
from apps.copywriting.models import CopywritingSession


class CopywritingSessionSerializer(serializers.ModelSerializer):
    """Serializer for CopywritingSession model."""
    final_outputs = serializers.SerializerMethodField()
    
    class Meta:
        model = CopywritingSession
        fields = [
            'id',
            'project',
            'inputs',
            'outputs',
            'edits',
            'final_outputs',
            'status',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'project',
            'inputs',
            'outputs',
            'edits',
            'final_outputs',
            'status',
            'created_at',
            'updated_at',
        ]
    
    def get_final_outputs(self, obj):
        """Get merged outputs with edits."""
        return obj.get_final_outputs()


class GenerateCopywritingSerializer(serializers.Serializer):
    """Serializer for generating copywriting."""
    description = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text='Optional user note or description'
    )


class EditSectionSerializer(serializers.Serializer):
    """Serializer for editing a section of copywriting."""
    section = serializers.CharField(
        required=True,
        help_text='Section name to edit (e.g., title, caption, cta)'
    )
    new_value = serializers.CharField(
        required=True,
        allow_blank=True,
        help_text='New value for the section'
    )


class RegenerateSectionSerializer(serializers.Serializer):
    """Serializer for regenerating a section of copywriting."""
    section = serializers.CharField(
        required=True,
        help_text='Section name to regenerate (e.g., caption, hashtags)'
    )
    instruction = serializers.CharField(
        required=True,
        help_text='Instructions for how to regenerate the section'
    )


class SaveFinalSerializer(serializers.Serializer):
    """Serializer for saving final copywriting outputs."""
    pass  # No input required, just triggers the save action


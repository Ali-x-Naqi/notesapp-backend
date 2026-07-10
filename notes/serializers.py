from rest_framework import serializers

from .models import Note


class NoteSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Note
        fields = ["id", "user", "title", "body", "created_at", "updated_at"]
        read_only_fields = ["id", "user", "created_at", "updated_at"]

from drf_spectacular.utils import OpenApiResponse, extend_schema
from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note
from .permissions import IsOwnerOrAdmin
from .schemas import NoteInput
from .serializers import NoteSerializer


def _pydantic_errors(exc: PydanticValidationError) -> dict:
    """Convert Pydantic v2 validation errors to a DRF-style field-keyed dict."""
    errors: dict = {}
    for err in exc.errors():
        field = err["loc"][0] if err["loc"] else "non_field_errors"
        errors.setdefault(str(field), []).append(err["msg"])
    return errors


class NoteListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=NoteSerializer(many=True))
    def get(self, request):
        if request.user.profile.is_admin:
            notes = Note.objects.select_related("user").all()
        else:
            notes = Note.objects.select_related("user").filter(user=request.user)
        return Response(NoteSerializer(notes, many=True).data)

    @extend_schema(
        request=NoteSerializer,
        responses={201: NoteSerializer, 400: OpenApiResponse(description="Validation error")},
    )
    def post(self, request):
        try:
            note_input = NoteInput(**request.data)
        except PydanticValidationError as exc:
            return Response(_pydantic_errors(exc), status=status.HTTP_400_BAD_REQUEST)

        serializer = NoteSerializer(data=note_input.model_dump())
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteDetailView(APIView):
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def _get_note(self, pk):
        try:
            return Note.objects.select_related("user").get(pk=pk)
        except Note.DoesNotExist:
            return None

    @extend_schema(responses={200: NoteSerializer, 404: OpenApiResponse(description="Not found")})
    def get(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, note)
        return Response(NoteSerializer(note).data)

    @extend_schema(
        request=NoteSerializer,
        responses={
            200: NoteSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Not found"),
        },
    )
    def put(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, note)
        try:
            note_input = NoteInput(**request.data)
        except PydanticValidationError as exc:
            return Response(_pydantic_errors(exc), status=status.HTTP_400_BAD_REQUEST)
        serializer = NoteSerializer(note, data=note_input.model_dump())
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(
        request=NoteSerializer,
        responses={
            200: NoteSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Not found"),
        },
    )
    def patch(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, note)
        serializer = NoteSerializer(note, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    @extend_schema(responses={204: None, 404: OpenApiResponse(description="Not found")})
    def delete(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        self.check_object_permissions(request, note)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

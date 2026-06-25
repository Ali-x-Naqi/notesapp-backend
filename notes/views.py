from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Note
from .serializers import NoteSerializer


class NoteListView(APIView):
    def get(self, request):
        notes = Note.objects.select_related("user").all()
        serializer = NoteSerializer(notes, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = NoteSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = request.user if request.user.is_authenticated else None
        serializer.save(user=user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class NoteDetailView(APIView):
    def _get_note(self, pk):
        try:
            return Note.objects.select_related("user").get(pk=pk)
        except Note.DoesNotExist:
            return None

    def get(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NoteSerializer(note)
        return Response(serializer.data)

    def put(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NoteSerializer(note, data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        serializer = NoteSerializer(note, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        note = self._get_note(pk)
        if note is None:
            return Response({"detail": "Not found."}, status=status.HTTP_404_NOT_FOUND)
        note.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

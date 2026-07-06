from pydantic import ValidationError as PydanticValidationError
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .schemas import RegisterInput
from .serializers import RegisterSerializer


def _pydantic_errors(exc: PydanticValidationError) -> dict:
    errors: dict = {}
    for err in exc.errors():
        field = err["loc"][0] if err["loc"] else "non_field_errors"
        errors.setdefault(str(field), []).append(err["msg"])
    return errors


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        try:
            RegisterInput(**request.data)
        except PydanticValidationError as exc:
            return Response(_pydantic_errors(exc), status=status.HTTP_400_BAD_REQUEST)

        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "username": user.username,
            },
            status=status.HTTP_201_CREATED,
        )

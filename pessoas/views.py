from rest_framework import mixins, status, viewsets
from rest_framework.response import Response

from .models import Person
from .serializers import PersonSerializer


POSSIBLE_DUPLICATE_CODE = "POSSIBLE_DUPLICATE"


class PersonViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = PersonSerializer
    queryset = Person.objects.all()
    http_method_names = ["get", "post", "patch", "head", "options"]

    def _possible_duplicate_response(self, duplicates):
        return Response(
            {
                "code": POSSIBLE_DUPLICATE_CODE,
                "message": (
                    "Encontramos uma pessoa com o mesmo nome completo "
                    "e data de nascimento."
                ),
                "candidates": [
                    {
                        "id": person.id,
                        "display_name": person.display_name,
                        "full_name": person.full_name,
                        "birth_date": person.birth_date.isoformat(),
                    }
                    for person in duplicates
                ],
            },
            status=status.HTTP_409_CONFLICT,
        )

    def _get_possible_duplicates(self, serializer):
        data = serializer.validated_data
        duplicates = Person.objects.possible_duplicates(
            full_name=data.get("full_name"),
            birth_date=data.get("birth_date"),
        )

        if serializer.instance is not None:
            duplicates = duplicates.exclude(pk=serializer.instance.pk)

        return duplicates

    def _requires_duplicate_confirmation(self, serializer):
        if serializer.instance is not None:
            submitted_fields = set(serializer.initial_data.keys())
            if not submitted_fields.intersection({"full_name", "birth_date"}):
                return None

        allow_possible_duplicate = serializer.validated_data.get(
            "allow_possible_duplicate",
            False,
        )
        duplicates = self._get_possible_duplicates(serializer)
        return duplicates if duplicates.exists() and not allow_possible_duplicate else None

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        duplicates = self._requires_duplicate_confirmation(serializer)

        if duplicates is not None:
            return self._possible_duplicate_response(duplicates)

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        duplicates = self._requires_duplicate_confirmation(serializer)

        if duplicates is not None:
            return self._possible_duplicate_response(duplicates)

        self.perform_update(serializer)
        return Response(serializer.data)

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        allow_possible_duplicate = data.get("allow_possible_duplicate", False)
        duplicates = Person.objects.possible_duplicates(
            full_name=data.get("full_name"),
            birth_date=data.get("birth_date"),
        )

        if duplicates.exists() and not allow_possible_duplicate:
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

        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

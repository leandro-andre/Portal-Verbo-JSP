from rest_framework import mixins, viewsets

from .models import Person
from .serializers import PersonSerializer


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

    def perform_create(self, serializer):
        data = serializer.validated_data
        Person.objects.possible_duplicates(
            full_name=data.get("full_name"),
            birth_date=data.get("birth_date"),
        )
        serializer.save()

from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone

from .models import ChurchJourney


CHURCH_JOURNEY_ALREADY_EXISTS = "CHURCH_JOURNEY_ALREADY_EXISTS"


class ChurchJourneyError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


def start_church_journey(person, *, started_at=None):
    if person is None:
        raise ValueError("Informe uma Person para iniciar a jornada eclesiastica.")

    try:
        person.church_journey
    except ObjectDoesNotExist:
        pass
    else:
        raise ChurchJourneyError(
            CHURCH_JOURNEY_ALREADY_EXISTS,
            "Esta pessoa ja possui uma jornada eclesiastica.",
        )

    return ChurchJourney.objects.create(
        person=person,
        started_at=started_at or timezone.localdate(),
    )

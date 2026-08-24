from dataclasses import dataclass

from django.db import IntegrityError

from .models import PersonUnavailability


INVALID_UNAVAILABILITY_DATE_RANGE = "INVALID_UNAVAILABILITY_DATE_RANGE"
INVALID_UNAVAILABILITY_TIME_RANGE = "INVALID_UNAVAILABILITY_TIME_RANGE"
UNAVAILABILITY_TIME_REQUIRES_SINGLE_DAY = "UNAVAILABILITY_TIME_REQUIRES_SINGLE_DAY"
UNAVAILABILITY_OVERLAP = "UNAVAILABILITY_OVERLAP"
INVALID_UNAVAILABILITY_TRANSITION = "INVALID_UNAVAILABILITY_TRANSITION"


class UnavailabilityError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message
        super().__init__(message)


@dataclass(frozen=True)
class PersonAvailabilityResult:
    available: bool
    conflicts: tuple[PersonUnavailability, ...]


def validate_unavailability_period(*, start_date, end_date, start_time=None, end_time=None):
    if end_date < start_date:
        raise UnavailabilityError(
            INVALID_UNAVAILABILITY_DATE_RANGE,
            "A data final nao pode ser anterior a data inicial.",
        )

    has_start_time = start_time is not None
    has_end_time = end_time is not None
    if has_start_time != has_end_time:
        raise UnavailabilityError(
            INVALID_UNAVAILABILITY_TIME_RANGE,
            "Informe hora inicial e hora final.",
        )

    if start_time is not None and start_date != end_date:
        raise UnavailabilityError(
            UNAVAILABILITY_TIME_REQUIRES_SINGLE_DAY,
            "Faixa horaria so pode ser usada em indisponibilidade de um unico dia.",
        )

    if start_time is not None and end_time <= start_time:
        raise UnavailabilityError(
            INVALID_UNAVAILABILITY_TIME_RANGE,
            "A hora final precisa ser posterior a hora inicial.",
        )


def unavailabilities_overlap(first, second):
    if first.end_date < second.start_date or second.end_date < first.start_date:
        return False

    if first.start_date != first.end_date or second.start_date != second.end_date:
        return True

    if first.is_full_day or second.is_full_day:
        return True

    return first.start_time < second.end_time and second.start_time < first.end_time


def get_unavailability_overlaps(unavailability):
    candidates = PersonUnavailability.objects.filter(
        person=unavailability.person,
        status=PersonUnavailability.Status.ACTIVE,
        start_date__lte=unavailability.end_date,
        end_date__gte=unavailability.start_date,
    )
    if unavailability.pk:
        candidates = candidates.exclude(pk=unavailability.pk)

    return [
        candidate
        for candidate in candidates
        if unavailabilities_overlap(unavailability, candidate)
    ]


def ensure_no_active_overlap(unavailability):
    overlaps = get_unavailability_overlaps(unavailability)
    if overlaps:
        raise UnavailabilityError(
            UNAVAILABILITY_OVERLAP,
            "Ja existe indisponibilidade ativa nesse periodo.",
        )


def build_unavailability(*, person, start_date, end_date, start_time=None, end_time=None, reason="", instance=None):
    unavailability = instance or PersonUnavailability(person=person)
    unavailability.person = person
    unavailability.start_date = start_date
    unavailability.end_date = end_date
    unavailability.start_time = start_time
    unavailability.end_time = end_time
    unavailability.reason = (reason or "").strip()
    return unavailability


def create_person_unavailability(*, person, start_date, end_date, start_time=None, end_time=None, reason=""):
    validate_unavailability_period(
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
    )
    unavailability = build_unavailability(
        person=person,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        reason=reason,
    )
    ensure_no_active_overlap(unavailability)
    try:
        unavailability.save()
    except IntegrityError as exc:
        raise UnavailabilityError(UNAVAILABILITY_OVERLAP, "Nao foi possivel salvar a indisponibilidade.") from exc
    return unavailability


def update_person_unavailability(unavailability, *, start_date, end_date, start_time=None, end_time=None, reason=""):
    if unavailability.status != PersonUnavailability.Status.ACTIVE:
        raise UnavailabilityError(
            INVALID_UNAVAILABILITY_TRANSITION,
            "Reative a indisponibilidade antes de editar.",
        )
    validate_unavailability_period(
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
    )
    unavailability = build_unavailability(
        person=unavailability.person,
        start_date=start_date,
        end_date=end_date,
        start_time=start_time,
        end_time=end_time,
        reason=reason,
        instance=unavailability,
    )
    ensure_no_active_overlap(unavailability)
    unavailability.save(update_fields=["start_date", "end_date", "start_time", "end_time", "reason", "updated_at"])
    return unavailability


def deactivate_unavailability(unavailability):
    if unavailability.status != PersonUnavailability.Status.ACTIVE:
        raise UnavailabilityError(
            INVALID_UNAVAILABILITY_TRANSITION,
            "Somente indisponibilidades ativas podem ser inativadas.",
        )
    unavailability.status = PersonUnavailability.Status.INACTIVE
    unavailability.save(update_fields=["status", "updated_at"])
    return unavailability


def reactivate_unavailability(unavailability):
    if unavailability.status != PersonUnavailability.Status.INACTIVE:
        raise UnavailabilityError(
            INVALID_UNAVAILABILITY_TRANSITION,
            "Somente indisponibilidades inativas podem ser reativadas.",
        )
    validate_unavailability_period(
        start_date=unavailability.start_date,
        end_date=unavailability.end_date,
        start_time=unavailability.start_time,
        end_time=unavailability.end_time,
    )
    ensure_no_active_overlap(unavailability)
    unavailability.status = PersonUnavailability.Status.ACTIVE
    unavailability.save(update_fields=["status", "updated_at"])
    return unavailability


def get_person_unavailability_conflicts(person, date, time=None):
    queryset = PersonUnavailability.objects.filter(
        person=person,
        status=PersonUnavailability.Status.ACTIVE,
        start_date__lte=date,
        end_date__gte=date,
    ).order_by("start_date", "start_time", "id")

    if time is None:
        return tuple(queryset)

    conflicts = []
    for unavailability in queryset:
        if unavailability.is_full_day:
            conflicts.append(unavailability)
        elif unavailability.start_time <= time < unavailability.end_time:
            conflicts.append(unavailability)
    return tuple(conflicts)


def get_person_availability(person, date, time=None):
    conflicts = get_person_unavailability_conflicts(person, date, time=time)
    return PersonAvailabilityResult(available=not conflicts, conflicts=conflicts)


def is_person_available(person, date, time=None):
    return get_person_availability(person, date, time=time).available

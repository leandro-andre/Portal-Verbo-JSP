from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import ChurchJourney, DiscipleshipClass, DiscipleshipEnrollment


CHURCH_JOURNEY_ALREADY_EXISTS = "CHURCH_JOURNEY_ALREADY_EXISTS"
DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS = "DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS"
INVALID_DISCIPLESHIP_CLASS_TRANSITION = "INVALID_DISCIPLESHIP_CLASS_TRANSITION"
PERSON_NOT_IN_CHURCH_JOURNEY = "PERSON_NOT_IN_CHURCH_JOURNEY"
DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT = "DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT"
DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS = "DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS"
INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION = "INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION"


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


def create_discipleship_class(*, name, teacher, start_date, expected_end_date, planned_sessions):
    return DiscipleshipClass.objects.create(
        name=name,
        teacher=teacher,
        start_date=start_date,
        expected_end_date=expected_end_date,
        planned_sessions=planned_sessions,
    )


def update_discipleship_class(
    discipleship_class,
    *,
    name=None,
    teacher=None,
    start_date=None,
    expected_end_date=None,
    planned_sessions=None,
):
    if discipleship_class.status in (
        DiscipleshipClass.Status.COMPLETED,
        DiscipleshipClass.Status.CANCELLED,
    ):
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_CLASS_TRANSITION,
            "Turmas concluidas ou canceladas nao podem ser editadas.",
        )

    if name is not None:
        discipleship_class.name = name
    if teacher is not None:
        discipleship_class.teacher = teacher
    if start_date is not None:
        discipleship_class.start_date = start_date
    if expected_end_date is not None:
        discipleship_class.expected_end_date = expected_end_date
    if planned_sessions is not None:
        discipleship_class.planned_sessions = planned_sessions

    discipleship_class.save()
    return discipleship_class


def start_discipleship_class(discipleship_class):
    if discipleship_class.status != DiscipleshipClass.Status.PLANNED:
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_CLASS_TRANSITION,
            "Somente turmas planejadas podem ser iniciadas.",
        )

    with transaction.atomic():
        if (
            DiscipleshipClass.objects.select_for_update()
            .filter(status=DiscipleshipClass.Status.IN_PROGRESS)
            .exclude(pk=discipleship_class.pk)
            .exists()
        ):
            raise ChurchJourneyError(
                DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS,
                "Ja existe uma turma de discipulado em andamento.",
            )

        discipleship_class.status = DiscipleshipClass.Status.IN_PROGRESS
        try:
            discipleship_class.save(update_fields=["status", "updated_at"])
        except IntegrityError as exc:
            raise ChurchJourneyError(
                DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS,
                "Ja existe uma turma de discipulado em andamento.",
            ) from exc

    return discipleship_class


def complete_discipleship_class(discipleship_class):
    if discipleship_class.status != DiscipleshipClass.Status.IN_PROGRESS:
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_CLASS_TRANSITION,
            "Somente turmas em andamento podem ser concluidas.",
        )

    discipleship_class.status = DiscipleshipClass.Status.COMPLETED
    discipleship_class.save(update_fields=["status", "updated_at"])
    return discipleship_class


def cancel_discipleship_class(discipleship_class):
    if discipleship_class.status not in (
        DiscipleshipClass.Status.PLANNED,
        DiscipleshipClass.Status.IN_PROGRESS,
    ):
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_CLASS_TRANSITION,
            "Somente turmas planejadas ou em andamento podem ser canceladas.",
        )

    discipleship_class.status = DiscipleshipClass.Status.CANCELLED
    discipleship_class.save(update_fields=["status", "updated_at"])
    return discipleship_class


def enroll_person_in_discipleship_class(*, person, discipleship_class):
    if not hasattr(person, "church_journey"):
        raise ChurchJourneyError(
            PERSON_NOT_IN_CHURCH_JOURNEY,
            "Esta pessoa ainda nao esta na jornada da igreja.",
        )

    if discipleship_class.status not in (
        DiscipleshipClass.Status.PLANNED,
        DiscipleshipClass.Status.IN_PROGRESS,
    ):
        raise ChurchJourneyError(
            DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT,
            "Esta turma nao esta aberta para matriculas.",
        )

    try:
        return DiscipleshipEnrollment.objects.create(
            person=person,
            discipleship_class=discipleship_class,
        )
    except IntegrityError as exc:
        raise ChurchJourneyError(
            DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS,
            "Esta pessoa ja possui matricula nesta turma.",
        ) from exc


def withdraw_discipleship_enrollment(enrollment):
    if enrollment.status != DiscipleshipEnrollment.Status.ENROLLED:
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION,
            "Somente matriculas ativas podem ser marcadas como desistentes.",
        )

    enrollment.status = DiscipleshipEnrollment.Status.WITHDRAWN
    enrollment.withdrawn_at = timezone.localdate()
    enrollment.save(update_fields=["status", "withdrawn_at", "updated_at"])
    return enrollment

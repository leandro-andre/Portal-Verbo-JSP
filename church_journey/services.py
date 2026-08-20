from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import (
    ChurchJourney,
    DiscipleshipAttendance,
    DiscipleshipClass,
    DiscipleshipEnrollment,
    DiscipleshipLesson,
)


CHURCH_JOURNEY_ALREADY_EXISTS = "CHURCH_JOURNEY_ALREADY_EXISTS"
DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS = "DISCIPLESHIP_CLASS_ALREADY_IN_PROGRESS"
INVALID_DISCIPLESHIP_CLASS_TRANSITION = "INVALID_DISCIPLESHIP_CLASS_TRANSITION"
PERSON_NOT_IN_CHURCH_JOURNEY = "PERSON_NOT_IN_CHURCH_JOURNEY"
DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT = "DISCIPLESHIP_CLASS_NOT_OPEN_FOR_ENROLLMENT"
DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS = "DISCIPLESHIP_ENROLLMENT_ALREADY_EXISTS"
INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION = "INVALID_DISCIPLESHIP_ENROLLMENT_TRANSITION"
DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS = "DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS"
DISCIPLESHIP_LESSON_DATE_CONFLICT = "DISCIPLESHIP_LESSON_DATE_CONFLICT"
INVALID_DISCIPLESHIP_LESSON_TRANSITION = "INVALID_DISCIPLESHIP_LESSON_TRANSITION"
DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH = "DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH"
DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE = (
    "DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE"
)
CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE = (
    "CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE"
)
DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON = (
    "DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON"
)
INVALID_DISCIPLESHIP_ATTENDANCE_STATUS = "INVALID_DISCIPLESHIP_ATTENDANCE_STATUS"


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


def ensure_class_open_for_lessons(discipleship_class):
    if discipleship_class.status not in (
        DiscipleshipClass.Status.PLANNED,
        DiscipleshipClass.Status.IN_PROGRESS,
    ):
        raise ChurchJourneyError(
            DISCIPLESHIP_CLASS_NOT_OPEN_FOR_LESSONS,
            "Esta turma nao esta aberta para gerenciamento de aulas.",
        )


def ensure_lesson_date_available(*, discipleship_class, lesson_date, lesson=None):
    conflicting_lessons = DiscipleshipLesson.objects.filter(
        discipleship_class=discipleship_class,
        lesson_date=lesson_date,
    )
    if lesson is not None:
        conflicting_lessons = conflicting_lessons.exclude(pk=lesson.pk)

    if conflicting_lessons.exists():
        raise ChurchJourneyError(
            DISCIPLESHIP_LESSON_DATE_CONFLICT,
            "Ja existe uma aula cadastrada para esta turma nesta data.",
        )


def create_discipleship_lesson(*, discipleship_class, title, lesson_date):
    ensure_class_open_for_lessons(discipleship_class)
    title = (title or "").strip()
    ensure_lesson_date_available(
        discipleship_class=discipleship_class,
        lesson_date=lesson_date,
    )

    lesson = DiscipleshipLesson(
        discipleship_class=discipleship_class,
        title=title,
        lesson_date=lesson_date,
    )
    lesson.full_clean(validate_unique=False)

    try:
        lesson.save()
        return lesson
    except IntegrityError as exc:
        raise ChurchJourneyError(
            DISCIPLESHIP_LESSON_DATE_CONFLICT,
            "Ja existe uma aula cadastrada para esta turma nesta data.",
        ) from exc


def update_discipleship_lesson(lesson, *, title=None, lesson_date=None):
    ensure_class_open_for_lessons(lesson.discipleship_class)

    if lesson.status == DiscipleshipLesson.Status.CANCELLED:
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_LESSON_TRANSITION,
            "Aulas canceladas nao podem ser editadas.",
        )

    if title is not None:
        lesson.title = (title or "").strip()
    if lesson_date is not None:
        ensure_lesson_date_available(
            discipleship_class=lesson.discipleship_class,
            lesson_date=lesson_date,
            lesson=lesson,
        )
        lesson.lesson_date = lesson_date

    try:
        lesson.full_clean()
        lesson.save(update_fields=["title", "lesson_date", "updated_at"])
    except IntegrityError as exc:
        raise ChurchJourneyError(
            DISCIPLESHIP_LESSON_DATE_CONFLICT,
            "Ja existe uma aula cadastrada para esta turma nesta data.",
        ) from exc

    return lesson


def cancel_discipleship_lesson(lesson):
    ensure_class_open_for_lessons(lesson.discipleship_class)

    if lesson.status != DiscipleshipLesson.Status.SCHEDULED:
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_LESSON_TRANSITION,
            "Somente aulas agendadas podem ser canceladas.",
        )

    lesson.status = DiscipleshipLesson.Status.CANCELLED
    lesson.save(update_fields=["status", "updated_at"])
    return lesson


def validate_attendance_status(status):
    valid_statuses = {choice[0] for choice in DiscipleshipAttendance.Status.choices}
    if status not in valid_statuses:
        raise ChurchJourneyError(
            INVALID_DISCIPLESHIP_ATTENDANCE_STATUS,
            "Informe um status de presenca valido.",
        )


def ensure_lesson_accepts_attendance(lesson):
    if lesson.status == DiscipleshipLesson.Status.CANCELLED:
        raise ChurchJourneyError(
            CANCELLED_DISCIPLESHIP_LESSON_DOES_NOT_ACCEPT_ATTENDANCE,
            "Aulas canceladas nao aceitam chamada.",
        )

    if lesson.lesson_date > timezone.localdate():
        raise ChurchJourneyError(
            DISCIPLESHIP_LESSON_NOT_YET_AVAILABLE_FOR_ATTENDANCE,
            "A chamada ainda nao esta disponivel para esta aula.",
        )


def is_enrollment_eligible_for_lesson(enrollment, lesson):
    if enrollment.discipleship_class_id != lesson.discipleship_class_id:
        return False

    if lesson.lesson_date < enrollment.enrolled_at:
        return False

    if enrollment.withdrawn_at and lesson.lesson_date > enrollment.withdrawn_at:
        return False

    return True


def ensure_enrollment_eligible_for_lesson(enrollment, lesson):
    if enrollment.discipleship_class_id != lesson.discipleship_class_id:
        raise ChurchJourneyError(
            DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH,
            "A matricula e a aula pertencem a turmas diferentes.",
        )

    if not is_enrollment_eligible_for_lesson(enrollment, lesson):
        raise ChurchJourneyError(
            DISCIPLESHIP_ENROLLMENT_NOT_ELIGIBLE_FOR_LESSON,
            "Esta matricula nao e elegivel para esta aula.",
        )


def get_eligible_enrollments_for_lesson(lesson):
    return (
        DiscipleshipEnrollment.objects.filter(
            Q(withdrawn_at__isnull=True) | Q(withdrawn_at__gte=lesson.lesson_date),
            discipleship_class=lesson.discipleship_class,
            enrolled_at__lte=lesson.lesson_date,
        )
        .select_related("person", "discipleship_class")
        .order_by("person__full_name", "id")
    )


def record_discipleship_attendance(*, enrollment, lesson, status, recorded_by=None):
    validate_attendance_status(status)
    ensure_lesson_accepts_attendance(lesson)
    ensure_enrollment_eligible_for_lesson(enrollment, lesson)

    try:
        attendance, _ = DiscipleshipAttendance.objects.update_or_create(
            enrollment=enrollment,
            lesson=lesson,
            defaults={
                "status": status,
                "recorded_by": recorded_by,
            },
        )
    except IntegrityError as exc:
        raise ChurchJourneyError(
            DISCIPLESHIP_ATTENDANCE_CLASS_MISMATCH,
            "Nao foi possivel registrar esta chamada.",
        ) from exc

    return attendance


def update_discipleship_attendance(attendance, *, status, recorded_by=None):
    return record_discipleship_attendance(
        enrollment=attendance.enrollment,
        lesson=attendance.lesson,
        status=status,
        recorded_by=recorded_by,
    )


def record_discipleship_attendance_batch(*, lesson, records, recorded_by=None):
    with transaction.atomic():
        attendances = []
        for record in records:
            attendances.append(
                record_discipleship_attendance(
                    enrollment=record["enrollment"],
                    lesson=lesson,
                    status=record["status"],
                    recorded_by=recorded_by,
                )
            )
        return attendances

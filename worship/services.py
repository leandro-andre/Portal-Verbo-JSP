from calendar import monthrange
from datetime import date, timedelta

from django.core.exceptions import ValidationError

from .models import WorshipService, WorshipServiceTemplate


class WorshipScheduleError(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code
        self.message = message


INVALID_TEMPLATE_TRANSITION = "INVALID_TEMPLATE_TRANSITION"
INVALID_SERVICE_TRANSITION = "INVALID_SERVICE_TRANSITION"


def create_worship_service_template(*, name, weekday, time):
    return WorshipServiceTemplate.objects.create(name=name, weekday=weekday, time=time)


def update_worship_service_template(template, *, name=None, weekday=None, time=None):
    if name is not None:
        template.name = name
    if weekday is not None:
        template.weekday = weekday
    if time is not None:
        template.time = time
    template.save(update_fields=["name", "weekday", "time", "updated_at"])
    return template


def deactivate_worship_service_template(template):
    if not template.active:
        raise WorshipScheduleError(INVALID_TEMPLATE_TRANSITION, "Este culto padrao ja esta inativo.")
    template.active = False
    template.save(update_fields=["active", "updated_at"])
    return template


def reactivate_worship_service_template(template):
    if template.active:
        raise WorshipScheduleError(INVALID_TEMPLATE_TRANSITION, "Este culto padrao ja esta ativo.")
    template.active = True
    template.save(update_fields=["active", "updated_at"])
    return template


def get_weekday_dates_for_month(*, year, month, weekday):
    _, last_day = monthrange(year, month)
    current = date(year, month, 1)
    while current.weekday() != int(weekday):
        current += timedelta(days=1)

    dates = []
    while current.month == month and current.day <= last_day:
        dates.append(current)
        current += timedelta(days=7)
    return dates


def generate_worship_services_for_month(*, year, month):
    created_count = 0
    existing_count = 0
    created_services = []

    for template in WorshipServiceTemplate.objects.active().ordered():
        for source_date in get_weekday_dates_for_month(year=year, month=month, weekday=template.weekday):
            service, created = WorshipService.objects.get_or_create(
                template=template,
                source_date=source_date,
                defaults={
                    "name": template.name,
                    "date": source_date,
                    "time": template.time,
                    "kind": WorshipService.Kind.REGULAR,
                    "status": WorshipService.Status.SCHEDULED,
                },
            )
            if created:
                created_count += 1
                created_services.append(service)
            else:
                existing_count += 1

    return {
        "created_count": created_count,
        "existing_count": existing_count,
        "created_services": created_services,
    }


def create_extraordinary_worship_service(*, name, date, time, notes=""):
    return WorshipService.objects.create(
        name=name,
        date=date,
        time=time,
        notes=notes,
        kind=WorshipService.Kind.EXTRAORDINARY,
        status=WorshipService.Status.SCHEDULED,
    )


def update_worship_service(service, *, name=None, date=None, time=None, notes=None):
    if name is not None:
        service.name = name
    if date is not None:
        service.date = date
    if time is not None:
        service.time = time
    if notes is not None:
        service.notes = notes
    service.save(update_fields=["name", "date", "time", "notes", "updated_at"])
    return service


def cancel_worship_service(service):
    if service.status == WorshipService.Status.CANCELLED:
        raise WorshipScheduleError(INVALID_SERVICE_TRANSITION, "Este culto ja esta cancelado.")
    service.status = WorshipService.Status.CANCELLED
    service.save(update_fields=["status", "updated_at"])
    return service


def reactivate_worship_service(service):
    if service.status == WorshipService.Status.SCHEDULED:
        raise WorshipScheduleError(INVALID_SERVICE_TRANSITION, "Este culto ja esta agendado.")
    service.status = WorshipService.Status.SCHEDULED
    service.save(update_fields=["status", "updated_at"])
    return service


def serializer_errors_to_validation_error(serializer):
    raise ValidationError(serializer.errors)

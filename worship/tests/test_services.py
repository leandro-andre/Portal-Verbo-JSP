from datetime import date, time

from django.core.exceptions import ValidationError
from django.test import TestCase

from worship.models import Weekday, WorshipService, WorshipServiceTemplate
from worship.services import (
    WorshipScheduleError,
    cancel_worship_service,
    create_extraordinary_worship_service,
    create_worship_service_template,
    deactivate_worship_service_template,
    generate_worship_services_for_month,
    reactivate_worship_service,
    reactivate_worship_service_template,
    update_worship_service,
    update_worship_service_template,
)


class WorshipServiceTemplateServiceTests(TestCase):
    def test_create_update_and_lifecycle_template(self):
        template = create_worship_service_template(
            name="Culto Domingo Manha",
            weekday=Weekday.SUNDAY,
            time=time(10, 0),
        )

        self.assertEqual(template.weekday, Weekday.SUNDAY)
        self.assertEqual(template.time, time(10, 0))
        self.assertTrue(template.active)
        self.assertEqual(template.get_weekday_display(), "Domingo")

        update_worship_service_template(template, name="Culto Domingo Noite", weekday=Weekday.SUNDAY, time=time(18, 0))
        template.refresh_from_db()
        self.assertEqual(template.name, "Culto Domingo Noite")
        self.assertEqual(template.time, time(18, 0))

        deactivate_worship_service_template(template)
        template.refresh_from_db()
        self.assertFalse(template.active)

        reactivate_worship_service_template(template)
        template.refresh_from_db()
        self.assertTrue(template.active)

    def test_invalid_template_lifecycle_is_rejected(self):
        template = create_worship_service_template(
            name="Culto Quinta",
            weekday=Weekday.THURSDAY,
            time=time(20, 0),
        )

        with self.assertRaises(WorshipScheduleError):
            reactivate_worship_service_template(template)

        deactivate_worship_service_template(template)
        with self.assertRaises(WorshipScheduleError):
            deactivate_worship_service_template(template)

    def test_delete_is_not_a_domain_operation(self):
        template = create_worship_service_template(
            name="Culto Domingo",
            weekday=Weekday.SUNDAY,
            time=time(10, 0),
        )
        deactivate_worship_service_template(template)

        self.assertTrue(WorshipServiceTemplate.objects.filter(pk=template.pk).exists())


class WorshipServiceGenerationTests(TestCase):
    def test_generates_sundays_for_september_2026(self):
        template = create_worship_service_template(
            name="Culto Domingo Manha",
            weekday=Weekday.SUNDAY,
            time=time(10, 0),
        )

        result = generate_worship_services_for_month(year=2026, month=9)

        self.assertEqual(result["created_count"], 4)
        self.assertEqual(result["existing_count"], 0)
        self.assertEqual(
            list(WorshipService.objects.values_list("source_date", flat=True)),
            [
                date(2026, 9, 6),
                date(2026, 9, 13),
                date(2026, 9, 20),
                date(2026, 9, 27),
            ],
        )
        service = WorshipService.objects.get(source_date=date(2026, 9, 6))
        self.assertEqual(service.template, template)
        self.assertEqual(service.kind, WorshipService.Kind.REGULAR)
        self.assertEqual(service.status, WorshipService.Status.SCHEDULED)

    def test_generation_is_idempotent(self):
        create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))

        first = generate_worship_services_for_month(year=2026, month=9)
        second = generate_worship_services_for_month(year=2026, month=9)

        self.assertEqual(first["created_count"], 4)
        self.assertEqual(second["created_count"], 0)
        self.assertEqual(second["existing_count"], 4)
        self.assertEqual(WorshipService.objects.count(), 4)

    def test_two_templates_on_same_day_are_generated(self):
        create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        create_worship_service_template(name="Culto Domingo Noite", weekday=Weekday.SUNDAY, time=time(18, 0))

        result = generate_worship_services_for_month(year=2026, month=9)

        self.assertEqual(result["created_count"], 8)
        self.assertEqual(WorshipService.objects.filter(source_date=date(2026, 9, 6)).count(), 2)

    def test_inactive_template_is_not_generated(self):
        template = create_worship_service_template(name="Culto Quinta", weekday=Weekday.THURSDAY, time=time(20, 0))
        deactivate_worship_service_template(template)

        result = generate_worship_services_for_month(year=2026, month=9)

        self.assertEqual(result["created_count"], 0)
        self.assertEqual(WorshipService.objects.count(), 0)

    def test_manual_time_change_is_preserved_after_regeneration(self):
        create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        generate_worship_services_for_month(year=2026, month=9)
        service = WorshipService.objects.get(source_date=date(2026, 9, 6))

        update_worship_service(service, time=time(11, 0))
        generate_worship_services_for_month(year=2026, month=9)
        service.refresh_from_db()

        self.assertEqual(service.time, time(11, 0))
        self.assertEqual(WorshipService.objects.filter(source_date=date(2026, 9, 6)).count(), 1)

    def test_manual_date_move_is_preserved_after_regeneration(self):
        create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        generate_worship_services_for_month(year=2026, month=9)
        service = WorshipService.objects.get(source_date=date(2026, 9, 6))

        update_worship_service(service, date=date(2026, 9, 7))
        generate_worship_services_for_month(year=2026, month=9)
        service.refresh_from_db()

        self.assertEqual(service.date, date(2026, 9, 7))
        self.assertEqual(WorshipService.objects.filter(template=service.template, source_date=date(2026, 9, 6)).count(), 1)

    def test_template_update_does_not_rewrite_existing_services(self):
        template = create_worship_service_template(name="Culto Domingo Manha", weekday=Weekday.SUNDAY, time=time(10, 0))
        generate_worship_services_for_month(year=2026, month=9)

        update_worship_service_template(template, name="Novo nome", time=time(9, 0))

        self.assertTrue(WorshipService.objects.filter(name="Culto Domingo Manha", time=time(10, 0)).exists())
        self.assertFalse(WorshipService.objects.filter(name="Novo nome", time=time(9, 0)).exists())


class ExtraordinaryWorshipServiceTests(TestCase):
    def test_extraordinary_service_has_no_template(self):
        service = create_extraordinary_worship_service(
            name="Conferencia de Fe",
            date=date(2026, 9, 19),
            time=time(19, 0),
            notes="Noite especial",
        )

        self.assertIsNone(service.template)
        self.assertIsNone(service.source_date)
        self.assertEqual(service.kind, WorshipService.Kind.EXTRAORDINARY)
        self.assertEqual(service.status, WorshipService.Status.SCHEDULED)

    def test_extraordinary_service_can_be_edited_cancelled_and_reactivated(self):
        service = create_extraordinary_worship_service(
            name="Conferencia de Fe",
            date=date(2026, 9, 19),
            time=time(19, 0),
        )

        update_worship_service(service, name="Conferencia de Fe - Noite 1", time=time(19, 30), notes="Ajustado")
        cancel_worship_service(service)
        service.refresh_from_db()
        self.assertEqual(service.name, "Conferencia de Fe - Noite 1")
        self.assertEqual(service.time, time(19, 30))
        self.assertEqual(service.status, WorshipService.Status.CANCELLED)

        reactivate_worship_service(service)
        service.refresh_from_db()
        self.assertEqual(service.status, WorshipService.Status.SCHEDULED)

    def test_regular_service_requires_template_and_source_date(self):
        with self.assertRaises(ValidationError):
            WorshipService.objects.create(
                name="Culto regular invalido",
                date=date(2026, 9, 6),
                time=time(10, 0),
                kind=WorshipService.Kind.REGULAR,
            )

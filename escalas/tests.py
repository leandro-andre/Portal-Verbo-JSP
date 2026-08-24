from datetime import date, time, timedelta
from io import StringIO

from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone

from departamentos.models import Departamento, DepartamentoMembro, DepartmentMembership, DepartmentRole
from pessoas.models import Person
from scheduling.models import Schedule
from worship.models import WorshipService

from .admin import CultoPadraoAdmin, EscalaAdmin, EscalaItemAdmin, IndisponibilidadeMembroAdmin
from .models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro


class LegacySchedulingReportTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(username="legacy.report", password="senha")
        self.person = Person.objects.create(full_name="Legacy Report", birth_date=date(1990, 1, 1))
        self.user.person = self.person
        self.user.save(update_fields=["person"])
        self.department = Departamento.objects.create(nome="Midia Report")
        self.role = DepartmentRole.objects.create(
            department=self.department,
            name="Operador",
            code="operador",
        )
        self.legacy_membership = DepartamentoMembro.objects.create(
            membro=self.user,
            departamento=self.department,
            papel=DepartamentoMembro.Papel.VOLUNTARIO,
        )
        DepartmentMembership.objects.create(
            person=self.person,
            department=self.department,
            role=self.role,
            status=DepartmentMembership.Status.ACTIVE,
        )

    def test_report_is_read_only_and_identifies_future_matches(self):
        worship_service = WorshipService.objects.create(
            name="Culto Report",
            date=timezone.localdate() + timedelta(days=10),
            time=time(19, 0),
            kind=WorshipService.Kind.EXTRAORDINARY,
            status=WorshipService.Status.SCHEDULED,
        )
        Schedule.objects.create(department=self.department, worship_service=worship_service)
        escala = Escala.objects.create(
            departamento=self.department,
            titulo="Escala Report",
            data=worship_service.date,
            horario=worship_service.time,
        )
        EscalaItem.objects.create(
            escala=escala,
            participacao=self.legacy_membership,
            funcao="Camera",
        )
        before_counts = {
            "cultos": CultoPadrao.objects.count(),
            "escalas": Escala.objects.count(),
            "itens": EscalaItem.objects.count(),
            "indisponibilidades": IndisponibilidadeMembro.objects.count(),
        }

        output = StringIO()
        call_command("legacy_scheduling_report", stdout=output)

        self.assertEqual(before_counts["cultos"], CultoPadrao.objects.count())
        self.assertEqual(before_counts["escalas"], Escala.objects.count())
        self.assertEqual(before_counts["itens"], EscalaItem.objects.count())
        self.assertEqual(before_counts["indisponibilidades"], IndisponibilidadeMembro.objects.count())
        report = output.getvalue()
        self.assertIn("Escalas futuras: 1", report)
        self.assertIn("MATCHED_WORSHIP_SERVICE", report)
        self.assertIn("POTENTIAL_DUPLICATE", report)
        self.assertIn("person_match=MATCHED", report)


class LegacySchedulingAdminTests(TestCase):
    def test_legacy_admin_models_are_read_only(self):
        user_model = get_user_model()
        superuser = user_model.objects.create_superuser(
            username="admin.legacy",
            email="admin.legacy@example.com",
            password="senha",
        )
        request = RequestFactory().get("/")
        request.user = superuser

        for model, admin_class in (
            (CultoPadrao, CultoPadraoAdmin),
            (Escala, EscalaAdmin),
            (EscalaItem, EscalaItemAdmin),
            (IndisponibilidadeMembro, IndisponibilidadeMembroAdmin),
        ):
            model_admin = admin_class(model, admin.site)
            self.assertFalse(model_admin.has_add_permission(request))
            self.assertFalse(model_admin.has_change_permission(request))
            self.assertFalse(model_admin.has_delete_permission(request))

        self.client.force_login(superuser)
        response = self.client.get(reverse("admin:escalas_escala_changelist"))
        self.assertEqual(response.status_code, 200)
        add_response = self.client.get(reverse("admin:escalas_escala_add"))
        self.assertEqual(add_response.status_code, 403)

from django.core.management.base import BaseCommand
from django.db.models import Count
from django.utils import timezone

from departamentos.models import DepartamentoMembro, DepartmentMembership
from escalas.models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro
from worship.models import WorshipService


class Command(BaseCommand):
    help = "Relatorio read-only do legado de escalas."

    def handle(self, *args, **options):
        today = timezone.localdate()
        legacy_future = (
            Escala.objects.filter(data__gte=today)
            .select_related("departamento", "culto_padrao")
            .annotate(total_pessoas=Count("itens", distinct=True))
            .order_by("data", "horario", "departamento__nome", "id")
        )

        self.stdout.write(f"CultosPadrao legado: {CultoPadrao.objects.count()}")
        self.stdout.write(f"Escalas legado totais: {Escala.objects.count()}")
        self.stdout.write(f"Escalas futuras: {legacy_future.count()}")
        self.stdout.write(f"Escalas passadas: {Escala.objects.filter(data__lt=today).count()}")
        self.stdout.write(f"EscalaItems: {EscalaItem.objects.count()}")
        self.stdout.write(f"IndisponibilidadeMembro legado: {IndisponibilidadeMembro.objects.count()}")
        self.stdout.write(
            "DepartamentoMembro sem Person: "
            f"{DepartamentoMembro.objects.filter(membro__person__isnull=True).count()}"
        )
        self.stdout.write(
            "Vinculos sem DepartmentMembership novo: "
            f"{self.count_legacy_memberships_without_new_match()}"
        )
        self.stdout.write("Escalas futuras detalhadas:")

        if not legacy_future.exists():
            self.stdout.write("- nenhuma")
            return

        for escala in legacy_future:
            worship_status = self.get_worship_service_status(escala)
            duplicate_status = self.get_duplicate_status(escala)
            self.stdout.write(
                "- "
                f"id={escala.id}; "
                f"departamento={escala.departamento.nome}; "
                f"data={escala.data:%Y-%m-%d}; "
                f"horario={escala.horario:%H:%M}; "
                f"culto_padrao={escala.culto_padrao.nome if escala.culto_padrao_id else '-'}; "
                f"pessoas={escala.total_pessoas}; "
                f"worship_service={worship_status}; "
                f"duplicate={duplicate_status}"
            )

            for item in escala.itens.select_related("participacao__membro", "participacao__departamento"):
                self.stdout.write(
                    "  item "
                    f"id={item.id}; "
                    f"usuario={item.participacao.membro.username}; "
                    f"person_match={self.get_membership_match_status(item.participacao)}"
                )

    def count_legacy_memberships_without_new_match(self):
        total = 0
        for participacao in DepartamentoMembro.objects.select_related("membro__person", "departamento"):
            person = getattr(participacao.membro, "person", None)
            if not person:
                continue
            if not DepartmentMembership.objects.filter(
                person=person,
                department=participacao.departamento,
            ).exists():
                total += 1
        return total

    def get_worship_service_status(self, escala):
        matches = WorshipService.objects.filter(date=escala.data, time=escala.horario)
        count = matches.count()
        if count == 0:
            return "NO_WORSHIP_SERVICE"
        if count == 1:
            return "MATCHED_WORSHIP_SERVICE"
        return "AMBIGUOUS_WORSHIP_SERVICE"

    def get_duplicate_status(self, escala):
        matches = WorshipService.objects.filter(
            date=escala.data,
            time=escala.horario,
            schedules__department=escala.departamento,
        )
        if matches.exists():
            return "POTENTIAL_DUPLICATE"
        return "NO_DUPLICATE"

    def get_membership_match_status(self, participacao):
        person = getattr(participacao.membro, "person", None)
        if not person:
            return "NO_PERSON"
        matches = DepartmentMembership.objects.filter(
            person=person,
            department=participacao.departamento,
        )
        count = matches.count()
        if count == 0:
            return "NO_NEW_DEPARTMENT_MEMBERSHIP"
        if count == 1:
            return "MATCHED"
        return "AMBIGUOUS"

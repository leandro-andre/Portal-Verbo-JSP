import os
import sys

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.db.transaction import atomic


class Command(BaseCommand):
    help = "Remove dados de teste em ambiente de desenvolvimento, preservando superusers por padrao."

    def add_arguments(self, parser):
        parser.add_argument(
            "--yes",
            action="store_true",
            help="Confirma a execucao sem prompt interativo.",
        )
        parser.add_argument(
            "--include-superusers",
            action="store_true",
            help="Tambem remove superusers. Use somente se houver outro acesso administrativo planejado.",
        )

    def handle(self, *args, **options):
        self._ensure_non_production()

        plan = self._delete_plan(include_superusers=options["include_superusers"])
        total = sum(count for _, _, count in plan)

        self.stdout.write("Reset de dados de teste em ambiente de desenvolvimento/teste.")
        for app_label, model_name, count in plan:
            self.stdout.write(f"- {app_label}.{model_name}: {count}")
        self.stdout.write(f"Total previsto: {total}")

        if not options["yes"]:
            confirmation = input("Digite RESET para confirmar: ")
            if confirmation != "RESET":
                self.stdout.write("Operacao cancelada.")
                return

        with atomic():
            for _, _, _, queryset in self._delete_plan(
                include_superusers=options["include_superusers"],
                include_querysets=True,
            ):
                queryset.delete()

        self.stdout.write(self.style.SUCCESS("Dados de teste removidos com sucesso."))

    def _ensure_non_production(self):
        django_env = os.environ.get("DJANGO_ENV", "dev").strip().lower()
        running_tests = "test" in sys.argv
        if django_env in {"prod", "production"} or (not settings.DEBUG and not running_tests):
            raise CommandError("Este comando e bloqueado em ambiente de producao.")

    def _delete_plan(self, *, include_superusers, include_querysets=False):
        from core.models import ContatoMensagem, Lider, SiteConfig, SobrePage
        from departamentos.models import Departamento, DepartamentoMembro
        from escalas.models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro
        from eventos.models import Evento, InscricaoEvento
        from financeiro.models import ConfiguracaoFinanceira, Contribuicao
        from governanca.models import ConteudoAuditLog
        from infantil.models import AulaSala, ChamadaResponsavel, Crianca, SalaInfantil, SalaMembro
        from ministros.models import FotoMinistro, Ministro
        from noticias.models import Noticia
        from pessoas.models import Person
        from verbo_no_lar.models import (
            CasaVerboNoLar,
            EscalaVerboNoLar,
            MaterialApoioVerboNoLar,
            ParticipanteVerboNoLar,
            RelatorioEncontroVerboNoLar,
        )

        UserModel = get_user_model()
        users = UserModel.objects.all()
        people = Person.objects.all()
        if not include_superusers:
            users = users.filter(is_superuser=False)
            people = people.exclude(user_account__is_superuser=True)

        entries = [
            (ConteudoAuditLog, ConteudoAuditLog.objects.all()),
            (Contribuicao, Contribuicao.objects.all()),
            (RelatorioEncontroVerboNoLar, RelatorioEncontroVerboNoLar.objects.all()),
            (MaterialApoioVerboNoLar, MaterialApoioVerboNoLar.objects.all()),
            (EscalaVerboNoLar, EscalaVerboNoLar.objects.all()),
            (ParticipanteVerboNoLar, ParticipanteVerboNoLar.objects.all()),
            (CasaVerboNoLar, CasaVerboNoLar.objects.all()),
            (FotoMinistro, FotoMinistro.objects.all()),
            (Ministro, Ministro.objects.all()),
            (InscricaoEvento, InscricaoEvento.objects.all()),
            (Evento, Evento.objects.all()),
            (ChamadaResponsavel, ChamadaResponsavel.objects.all()),
            (AulaSala, AulaSala.objects.all()),
            (Crianca, Crianca.objects.all()),
            (SalaMembro, SalaMembro.objects.all()),
            (SalaInfantil, SalaInfantil.objects.all()),
            (EscalaItem, EscalaItem.objects.all()),
            (Escala, Escala.objects.all()),
            (CultoPadrao, CultoPadrao.objects.all()),
            (IndisponibilidadeMembro, IndisponibilidadeMembro.objects.all()),
            (DepartamentoMembro, DepartamentoMembro.objects.all()),
            (Departamento, Departamento.objects.all()),
            (Noticia, Noticia.objects.all()),
            (Lider, Lider.objects.all()),
            (ContatoMensagem, ContatoMensagem.objects.all()),
            (SobrePage, SobrePage.objects.all()),
            (SiteConfig, SiteConfig.objects.all()),
            (UserModel, users),
            (Person, people),
            (ConfiguracaoFinanceira, ConfiguracaoFinanceira.objects.all()),
        ]

        plan = []
        for model, queryset in entries:
            item = (model._meta.app_label, model.__name__, queryset.count())
            if include_querysets:
                item = (*item, queryset)
            plan.append(item)
        return plan

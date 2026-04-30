from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count, Prefetch, Q

from departamentos.models import Departamento, DepartamentoMembro


class IndisponibilidadeMembro(models.Model):
    class QuerySet(models.QuerySet):
        def do_membro(self, membro):
            return self.filter(membro=membro)

        def ativas(self):
            return self.filter(ativo=True)

        def recentes_primeiro(self):
            return self.order_by("-ativo", "-data_inicio", "-criado_em")

    objects = QuerySet.as_manager()

    membro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Membro",
        on_delete=models.PROTECT,
        related_name="indisponibilidades_escala",
    )
    data_inicio = models.DateField("Data inicial")
    data_fim = models.DateField("Data final")
    horario_inicio = models.TimeField("Horario inicial", blank=True, null=True)
    horario_fim = models.TimeField("Horario final", blank=True, null=True)
    motivo = models.TextField("Motivo", blank=True)
    ativo = models.BooleanField("Ativa", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-data_inicio", "-horario_inicio", "-criado_em"]
        verbose_name = "Indisponibilidade do membro"
        verbose_name_plural = "Indisponibilidades dos membros"
        db_table = "departamentos_indisponibilidademembro"

    def __str__(self):
        return f"{self.membro} - {self.periodo_label}"

    @property
    def periodo_label(self):
        data_inicio = self.data_inicio.strftime("%d/%m/%Y")
        data_fim = self.data_fim.strftime("%d/%m/%Y")
        if self.horario_inicio and self.horario_fim:
            horario = f" das {self.horario_inicio.strftime('%H:%M')} as {self.horario_fim.strftime('%H:%M')}"
        else:
            horario = ""

        if self.data_inicio == self.data_fim:
            return f"{data_inicio}{horario}"
        return f"{data_inicio} ate {data_fim}{horario}"

    def clean(self):
        super().clean()
        errors = {}

        if self.data_fim and self.data_inicio and self.data_fim < self.data_inicio:
            errors["data_fim"] = "A data final nao pode ser menor que a data inicial."

        if self.horario_inicio and not self.horario_fim:
            errors["horario_fim"] = "Informe o horario final quando houver horario inicial."

        if self.horario_fim and not self.horario_inicio:
            errors["horario_inicio"] = "Informe o horario inicial quando houver horario final."

        if (
            self.horario_inicio
            and self.horario_fim
            and self.horario_fim < self.horario_inicio
        ):
            errors["horario_fim"] = "O horario final nao pode ser menor que o horario inicial."

        if errors:
            raise ValidationError(errors)

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)


class CultoPadrao(models.Model):
    class DiaSemana(models.IntegerChoices):
        SEGUNDA = 0, "Segunda-feira"
        TERCA = 1, "Terca-feira"
        QUARTA = 2, "Quarta-feira"
        QUINTA = 3, "Quinta-feira"
        SEXTA = 4, "Sexta-feira"
        SABADO = 5, "Sabado"
        DOMINGO = 6, "Domingo"

    class QuerySet(models.QuerySet):
        def ativos(self):
            return self.filter(ativo=True)

        def por_nome(self, query):
            return self.filter(nome__icontains=query) if query else self

        def por_status(self, status):
            if status == "ativos":
                return self.ativos()
            if status == "inativos":
                return self.filter(ativo=False)
            return self

        def ordenados(self):
            return self.order_by("dia_semana", "horario", "nome")

    objects = QuerySet.as_manager()

    nome = models.CharField("Nome do culto", max_length=120, unique=True)
    dia_semana = models.PositiveSmallIntegerField(
        "Dia da semana",
        choices=DiaSemana.choices,
    )
    horario = models.TimeField("Horario")
    ativo = models.BooleanField("Ativo", default=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["dia_semana", "horario", "nome"]
        verbose_name = "Culto padrao"
        verbose_name_plural = "Cultos padrao"
        db_table = "departamentos_cultopadrao"
        constraints = [
            models.UniqueConstraint(
                fields=["dia_semana", "horario"],
                condition=Q(ativo=True),
                name="uniq_culto_padrao_ativo_por_dia_horario",
            )
        ]

    def __str__(self):
        return f"{self.nome} - {self.get_dia_semana_display()} ({self.horario.strftime('%H:%M')})"


class Escala(models.Model):
    class QuerySet(models.QuerySet):
        def com_relacoes_basicas(self):
            return self.select_related("departamento", "culto_padrao")

        def com_totais_itens(self):
            return self.annotate(total_itens_count=Count("itens", distinct=True))

        def com_itens_prefetch(self):
            return self.prefetch_related(
                Prefetch(
                    "itens",
                    queryset=EscalaItem.objects.com_relacoes_basicas(),
                )
            )

        def gerenciaveis_por_usuario(self, usuario, departamentos_queryset):
            if getattr(usuario, "is_superuser", False):
                return self
            return self.filter(departamento__in=departamentos_queryset)

        def ativas(self):
            return self.filter(ativa=True)

        def por_titulo(self, query):
            return self.filter(titulo__icontains=query) if query else self

        def por_status(self, status):
            if status == "ativas":
                return self.ativas()
            if status == "inativas":
                return self.filter(ativa=False)
            return self

        def por_departamento_id(self, departamento_id):
            return self.filter(departamento_id=departamento_id) if departamento_id else self

        def futuras(self, data):
            return self.filter(data__gte=data)

    objects = QuerySet.as_manager()

    departamento = models.ForeignKey(
        Departamento,
        verbose_name="Departamento",
        on_delete=models.PROTECT,
        related_name="escalas",
    )
    culto_padrao = models.ForeignKey(
        CultoPadrao,
        verbose_name="Culto padrao",
        on_delete=models.SET_NULL,
        related_name="escalas",
        blank=True,
        null=True,
    )
    titulo = models.CharField("Titulo", max_length=150)
    data = models.DateField("Data")
    horario = models.TimeField("Horario")
    observacoes = models.TextField("Observacoes", blank=True)
    ativa = models.BooleanField("Ativa", default=True)
    criada_em = models.DateTimeField("Criada em", auto_now_add=True)

    class Meta:
        ordering = ["data", "horario", "titulo"]
        verbose_name = "Escala"
        verbose_name_plural = "Escalas"
        db_table = "departamentos_escala"
        constraints = [
            models.UniqueConstraint(
                fields=["departamento", "data", "horario"],
                name="uniq_escala_por_departamento_data_horario",
            )
        ]

    def __str__(self):
        data_str = self.data.strftime("%d/%m/%Y") if self.data else "Sem data"
        return f"{self.titulo} - {self.departamento} ({data_str})"

    @property
    def total_pessoas_escaladas(self):
        itens = getattr(self, "_prefetched_objects_cache", {}).get("itens")
        if itens is None:
            return self.itens.count()
        return len(itens)

    @property
    def eh_personalizada(self):
        return self.culto_padrao_id is None

    def clean(self):
        super().clean()
        errors = {}

        if self.culto_padrao_id and self.data:
            if self.data.weekday() != self.culto_padrao.dia_semana:
                errors["data"] = (
                    "A data escolhida precisa corresponder ao dia da semana do culto padrao."
                )
        if self.culto_padrao_id and self.horario and self.horario != self.culto_padrao.horario:
            errors["horario"] = "O horario precisa corresponder ao horario do culto padrao selecionado."

        if self.departamento_id and self.data and self.horario:
            duplicada = Escala.objects.filter(
                departamento_id=self.departamento_id,
                data=self.data,
                horario=self.horario,
            ).exclude(pk=self.pk)
            if duplicada.exists():
                errors["data"] = "Ja existe uma escala para este departamento na mesma data e horario."

        if errors:
            raise ValidationError(errors)


class EscalaItem(models.Model):
    class QuerySet(models.QuerySet):
        def com_relacoes_basicas(self):
            return self.select_related(
                "participacao__membro",
                "participacao__departamento",
                "escala",
                "escala__departamento",
            )

        def da_escala(self, escala):
            return self.filter(escala=escala)

        def do_membro(self, membro):
            return self.filter(participacao__membro=membro)

        def participacoes_ativas(self):
            return self.filter(participacao__ativo=True)

        def escalas_ativas(self):
            return self.filter(escala__ativa=True)

        def proximas_do_membro(self, membro, data):
            return (
                self.do_membro(membro)
                .participacoes_ativas()
                .escalas_ativas()
                .filter(escala__data__gte=data)
            )

        def confirmados(self):
            return self.filter(confirmado=True)

        def pendentes_confirmacao(self):
            return self.filter(confirmado=False)

        def ordenados_para_exibicao(self):
            return self.order_by(
                "funcao",
                "participacao__membro__first_name",
                "participacao__membro__username",
            )

    objects = QuerySet.as_manager()

    escala = models.ForeignKey(
        Escala,
        verbose_name="Escala",
        on_delete=models.CASCADE,
        related_name="itens",
    )
    participacao = models.ForeignKey(
        DepartamentoMembro,
        verbose_name="Membro escalado",
        on_delete=models.PROTECT,
        related_name="itens_escala",
    )
    funcao = models.CharField("Funcao na escala", max_length=120)
    confirmado = models.BooleanField("Confirmado", default=False)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["escala__data", "escala__horario", "funcao", "participacao__membro__first_name"]
        verbose_name = "Item da escala"
        verbose_name_plural = "Itens da escala"
        db_table = "departamentos_escalaitem"
        constraints = [
            models.UniqueConstraint(
                fields=["escala", "participacao"],
                name="uniq_participacao_por_escala",
            )
        ]

    def __str__(self):
        return f"{self.participacao.membro} - {self.funcao}"

    def clean(self):
        super().clean()
        if self.escala_id and self.participacao_id:
            from .utils import membro_esta_indisponivel

            if not self.participacao.ativo:
                raise ValidationError(
                    {
                        "participacao": (
                            "O membro escolhido precisa ter um vinculo ativo com o departamento da escala."
                        )
                    }
                )
            if self.participacao.departamento_id != self.escala.departamento_id:
                raise ValidationError(
                    {
                        "participacao": (
                            "O membro escalado precisa estar vinculado ao mesmo departamento da escala."
                        )
                    }
                )
            if self.escala.data and self.escala.horario:
                conflito = (
                    EscalaItem.objects.filter(
                        participacao__membro=self.participacao.membro,
                        escala__data=self.escala.data,
                        escala__horario=self.escala.horario,
                        escala__ativa=True,
                    )
                    .exclude(pk=self.pk)
                    .exclude(escala_id=self.escala_id)
                    .select_related("escala__departamento")
                    .first()
                )
                if conflito:
                    data_str = conflito.escala.data.strftime("%d/%m/%Y")
                    horario_str = conflito.escala.horario.strftime("%H:%M")
                    raise ValidationError(
                        {
                            "participacao": (
                                "Este membro ja esta escalado em "
                                f"{conflito.escala.departamento.nome} em {data_str} as {horario_str}."
                            )
                        }
                    )
                if membro_esta_indisponivel(
                    self.participacao.membro,
                    self.escala.data,
                    self.escala.horario,
                ):
                    raise ValidationError(
                        {
                            "participacao": (
                                "Este membro esta indisponivel para servir na data e horario desta escala."
                            )
                        }
                    )

    def save(self, *args, **kwargs):
        self.full_clean()
        return super().save(*args, **kwargs)

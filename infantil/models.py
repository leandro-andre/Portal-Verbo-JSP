from datetime import date

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.functions import Coalesce
from django.utils import timezone


class SalaInfantil(models.Model):
    nome = models.CharField("Nome", max_length=120, unique=True)
    descricao = models.TextField("Descricao", blank=True)
    idade_minima = models.PositiveSmallIntegerField("Idade minima")
    idade_maxima = models.PositiveSmallIntegerField("Idade maxima")
    ativa = models.BooleanField("Ativa", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["idade_minima", "idade_maxima", "nome"]
        verbose_name = "Sala infantil"
        verbose_name_plural = "Salas infantis"

    def __str__(self):
        return self.nome

    @property
    def faixa_etaria_label(self):
        return f"{self.idade_minima} a {self.idade_maxima} anos"

    def clean(self):
        super().clean()
        if self.idade_minima > self.idade_maxima:
            raise ValidationError(
                {
                    "idade_maxima": "A idade maxima precisa ser maior ou igual a idade minima.",
                }
            )


class SalaMembro(models.Model):
    class Papel(models.TextChoices):
        LIDER_SALA = "lider_sala", "Lider de sala"
        PROFESSOR = "professor", "Professor"
        AUXILIAR = "auxiliar", "Auxiliar"
        APOIO = "apoio", "Apoio"

    PAPEIS_GESTAO_SALA = (Papel.LIDER_SALA,)

    membro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Membro",
        on_delete=models.PROTECT,
        related_name="participacoes_salas_infantis",
    )
    sala = models.ForeignKey(
        SalaInfantil,
        verbose_name="Sala",
        on_delete=models.CASCADE,
        related_name="equipe",
    )
    papel = models.CharField(
        "Papel na sala",
        max_length=20,
        choices=Papel.choices,
        default=Papel.AUXILIAR,
    )
    ativo = models.BooleanField("Ativo", default=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["sala__nome", "papel", "membro__first_name", "membro__username"]
        verbose_name = "Membro da sala"
        verbose_name_plural = "Membros da sala"
        constraints = [
            models.UniqueConstraint(
                fields=["membro", "sala"],
                condition=Q(ativo=True),
                name="uniq_membro_ativo_por_sala",
            )
        ]

    def __str__(self):
        return f"{self.membro} - {self.sala} ({self.get_papel_display()})"


class Crianca(models.Model):
    class Sexo(models.TextChoices):
        MASCULINO = "masculino", "Masculino"
        FEMININO = "feminino", "Feminino"
        OUTRO = "outro", "Outro"

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADO = "aprovado", "Aprovado"
        RECUSADO = "recusado", "Recusado"
        INATIVO = "inativo", "Inativo"

    class QuerySet(models.QuerySet):
        def com_relacoes_basicas(self):
            return self.select_related("responsavel_usuario", "sala")

        def do_responsavel(self, usuario):
            return self.filter(responsavel_usuario=usuario)

        def pendentes(self):
            return self.filter(status=Crianca.Status.PENDENTE)

        def aprovadas(self):
            return self.filter(status=Crianca.Status.APROVADO)

        def recusadas(self):
            return self.filter(status=Crianca.Status.RECUSADO)

        def ativas(self):
            return self.filter(ativo=True)

        def da_sala(self, sala):
            return self.filter(sala=sala)

        def recentes_primeiro(self):
            return self.order_by("-criado_em")

    objects = QuerySet.as_manager()

    nome = models.CharField("Nome", max_length=150)
    data_nascimento = models.DateField("Data de nascimento")
    sexo = models.CharField("Sexo", max_length=20, choices=Sexo.choices, blank=True)
    responsavel_usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Responsavel usuario",
        on_delete=models.SET_NULL,
        related_name="criancas_cadastradas",
        blank=True,
        null=True,
    )
    responsavel_nome = models.CharField("Responsavel", max_length=150)
    responsavel_telefone = models.CharField("Telefone do responsavel", max_length=20)
    responsavel_email = models.EmailField("E-mail do responsavel", blank=True)
    sala = models.ForeignKey(
        SalaInfantil,
        verbose_name="Sala",
        on_delete=models.PROTECT,
        related_name="criancas",
        blank=True,
        null=True,
    )
    status = models.CharField(
        "Status do cadastro",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    observacoes_gerais = models.TextField("Observacoes gerais", blank=True)
    alergias = models.TextField("Alergias", blank=True)
    restricoes_alimentares = models.TextField("Restricoes alimentares", blank=True)
    necessidades_especiais = models.TextField("Necessidades especiais", blank=True)
    pode_comer_lanche_igreja = models.BooleanField("Pode comer lanche da igreja?", default=True)
    medicacao_ou_cuidado_especial = models.TextField(
        "Medicacao ou cuidado especial",
        blank=True,
    )
    observacao_para_professor = models.TextField(
        "Observacao para o professor",
        blank=True,
    )
    ativo = models.BooleanField("Ativa", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Crianca"
        verbose_name_plural = "Criancas"

    def __str__(self):
        return self.nome

    @property
    def idade_atual(self):
        hoje = timezone.localdate()
        anos = hoje.year - self.data_nascimento.year
        if (hoje.month, hoje.day) < (self.data_nascimento.month, self.data_nascimento.day):
            anos -= 1
        return anos

    @property
    def possui_alertas(self):
        return bool(
            (self.alergias or "").strip()
            or (self.restricoes_alimentares or "").strip()
            or (self.necessidades_especiais or "").strip()
            or (self.medicacao_ou_cuidado_especial or "").strip()
            or (self.observacao_para_professor or "").strip()
        )

    @property
    def status_badge_modifier(self):
        return {
            self.Status.PENDENTE: "warning",
            self.Status.APROVADO: "success",
            self.Status.RECUSADO: "muted",
            self.Status.INATIVO: "muted",
        }.get(self.status, "muted")

    @property
    def pode_ser_editada_pelo_responsavel(self):
        return self.status in {self.Status.PENDENTE, self.Status.RECUSADO}

    def clean(self):
        super().clean()
        if self.data_nascimento > date.today():
            raise ValidationError(
                {"data_nascimento": "A data de nascimento nao pode estar no futuro."}
            )
        if self.status == self.Status.APROVADO and not self.sala:
            raise ValidationError(
                {"sala": "Selecione uma sala para aprovar o cadastro da crianca."}
            )


class AulaSala(models.Model):
    sala = models.ForeignKey(
        SalaInfantil,
        verbose_name="Sala",
        on_delete=models.CASCADE,
        related_name="aulas",
    )
    data = models.DateField("Data")
    tema = models.CharField("Tema da aula", max_length=200)
    texto_base = models.CharField("Texto base", max_length=200, blank=True)
    conteudo_licao = models.TextField("Conteudo da licao", blank=True)
    anexo_licao = models.FileField(
        "Anexo da licao",
        upload_to="infantil/licoes/",
        blank=True,
        null=True,
    )
    observacoes = models.TextField("Observacoes", blank=True)
    criada_em = models.DateTimeField("Criada em", auto_now_add=True)

    class Meta:
        ordering = ["-data", "sala__nome"]
        verbose_name = "Aula da sala"
        verbose_name_plural = "Aulas das salas"
        constraints = [
            models.UniqueConstraint(
                fields=["sala", "data"],
                name="uniq_aula_por_sala_e_data",
            )
        ]

    def __str__(self):
        data_str = self.data.strftime("%d/%m/%Y") if self.data else "Sem data"
        return f"{self.sala} - {self.tema} ({data_str})"

    def clean(self):
        super().clean()
        if not (self.conteudo_licao or "").strip() and not self.anexo_licao:
            raise ValidationError(
                {
                    "conteudo_licao": (
                        "Informe o conteudo da licao ou envie um anexo para a aula."
                    )
                }
            )


class ChamadaResponsavel(models.Model):
    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        EXIBIDO = "exibido", "Exibido"
        RESOLVIDO = "resolvido", "Resolvido"
        CANCELADO = "cancelado", "Cancelado"

    class QuerySet(models.QuerySet):
        def com_relacoes_basicas(self):
            return self.select_related("sala", "criado_por")

        def da_sala(self, sala):
            return self.filter(sala=sala)

        def ativas(self):
            return self.filter(
                status__in=(
                    ChamadaResponsavel.Status.PENDENTE,
                    ChamadaResponsavel.Status.EXIBIDO,
                )
            )

        def pendentes(self):
            return self.filter(status=ChamadaResponsavel.Status.PENDENTE)

        def exibidas(self):
            return self.filter(status=ChamadaResponsavel.Status.EXIBIDO)

        def com_ultima_solicitacao(self):
            return self.annotate(
                ultima_solicitacao_em=Coalesce("reenviado_em", "criado_em")
            )

        def ordenadas_por_solicitacao(self):
            return self.com_ultima_solicitacao().order_by(
                "-ultima_solicitacao_em",
                "-criado_em",
            )

    objects = QuerySet.as_manager()

    sala = models.ForeignKey(
        SalaInfantil,
        verbose_name="Sala",
        on_delete=models.CASCADE,
        related_name="chamadas_responsavel",
    )
    numero_ficha = models.CharField("Numero da ficha", max_length=20)
    observacao = models.TextField("Observacao", blank=True)
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )
    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Criado por",
        on_delete=models.SET_NULL,
        related_name="chamadas_responsavel_criadas",
        null=True,
        blank=True,
    )
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    exibido_em = models.DateTimeField("Exibido em", blank=True, null=True)
    resolvido_em = models.DateTimeField("Resolvido em", blank=True, null=True)
    cancelado_em = models.DateTimeField("Cancelado em", blank=True, null=True)
    reenviado_em = models.DateTimeField("Reenviado em", blank=True, null=True)

    class Meta:
        ordering = ["status", "-criado_em"]
        verbose_name = "Chamada de responsavel"
        verbose_name_plural = "Chamadas de responsavel"

    def __str__(self):
        return f"{self.sala} - Ficha {self.numero_ficha}"

    @property
    def status_badge_modifier(self):
        return {
            self.Status.PENDENTE: "warning",
            self.Status.EXIBIDO: "info",
            self.Status.RESOLVIDO: "success",
            self.Status.CANCELADO: "muted",
        }.get(self.status, "muted")

    @property
    def esta_ativa(self):
        return self.status in {self.Status.PENDENTE, self.Status.EXIBIDO}

    @property
    def solicitada_em(self):
        return self.reenviado_em or self.criado_em

    def clean(self):
        super().clean()
        self.numero_ficha = (self.numero_ficha or "").strip()
        if not self.numero_ficha:
            raise ValidationError({"numero_ficha": "Informe o numero da ficha."})

    def marcar_exibido(self):
        self.status = self.Status.EXIBIDO
        self.exibido_em = timezone.now()
        self.save(update_fields=["status", "exibido_em"])

    def marcar_resolvido(self):
        self.status = self.Status.RESOLVIDO
        self.resolvido_em = timezone.now()
        self.save(update_fields=["status", "resolvido_em"])

    def marcar_cancelado(self):
        self.status = self.Status.CANCELADO
        self.cancelado_em = timezone.now()
        self.save(update_fields=["status", "cancelado_em"])

    def marcar_reenviado(self):
        self.status = self.Status.PENDENTE
        self.reenviado_em = timezone.now()
        self.save(update_fields=["status", "reenviado_em"])

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.utils import timezone
from django.utils.text import slugify


class Departamento(models.Model):
    CODIGO_MAX_LENGTH = 60

    class CodigoSistema:
        SECRETARIA = "secretaria"
        MIDIA = "midia"
        INFANTIL = "infantil"

        RESERVADOS = {
            SECRETARIA,
            MIDIA,
            INFANTIL,
        }

    CODIGO_PADRAO_MAP = {
        "secretaria": CodigoSistema.SECRETARIA,
        "departamento-de-secretaria": CodigoSistema.SECRETARIA,
        "midia": CodigoSistema.MIDIA,
        "departamento-de-midia": CodigoSistema.MIDIA,
        "infantil": CodigoSistema.INFANTIL,
        "departamento-infantil": CodigoSistema.INFANTIL,
    }

    nome = models.CharField("Nome", max_length=120, unique=True)
    codigo = models.SlugField(
        "Codigo interno",
        max_length=60,
        unique=True,
        db_index=False,
        blank=True,
        help_text=(
            "Identificador interno estavel usado por permissoes e integracoes. "
            "Se ficar vazio, o sistema gera automaticamente."
        ),
    )
    descricao = models.TextField("Descricao", blank=True)
    membros = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="DepartamentoMembro",
        related_name="departamentos",
        blank=True,
    )
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Departamento"
        verbose_name_plural = "Departamentos"
        permissions = [
            ("deactivate_departamento", "Can deactivate departamento"),
            ("reactivate_departamento", "Can reactivate departamento"),
        ]

    def __str__(self):
        return self.nome

    @classmethod
    def normalizar_codigo(cls, value):
        return slugify((value or "").strip())

    @classmethod
    def sugerir_codigo(cls, nome):
        slug_nome = cls.normalizar_codigo(nome)
        return cls.CODIGO_PADRAO_MAP.get(slug_nome, slug_nome)

    @classmethod
    def ajustar_codigo_ao_limite(cls, base_codigo, contador=None):
        max_length = cls._meta.get_field("codigo").max_length or cls.CODIGO_MAX_LENGTH
        if contador is None:
            return base_codigo[:max_length]

        sufixo = f"-{contador}"
        return f"{base_codigo[: max_length - len(sufixo)]}{sufixo}"

    @classmethod
    def gerar_codigo_departamento(cls, nome, codigo_base=""):
        base_codigo = cls.normalizar_codigo(codigo_base) or cls.sugerir_codigo(nome)
        if not base_codigo:
            base_codigo = "departamento"
        return cls.ajustar_codigo_ao_limite(base_codigo)

    def gerar_codigo_unico(self):
        base_codigo = self.gerar_codigo_departamento(self.nome, self.codigo)
        codigo = base_codigo
        contador = 2
        queryset = Departamento.objects.exclude(pk=self.pk)
        while queryset.filter(codigo=codigo).exists():
            codigo = self.ajustar_codigo_ao_limite(base_codigo, contador)
            contador += 1
        return codigo

    @property
    def lider_principal(self):
        participacoes = getattr(self, "_prefetched_objects_cache", {}).get("participacoes")
        if participacoes is None:
            participacoes = self.participacoes.select_related("membro")

        for participacao in participacoes:
            if participacao.ativo and participacao.papel == DepartamentoMembro.Papel.LIDER:
                return participacao.membro
        return None

    @property
    def total_membros_ativos(self):
        participacoes = getattr(self, "_prefetched_objects_cache", {}).get("participacoes")
        if participacoes is None:
            return self.participacoes.filter(ativo=True).count()
        return sum(1 for participacao in participacoes if participacao.ativo)

    def pode_gerenciar_escalas(self, user, allowed_roles=None):
        if not user.is_authenticated:
            return False
        from usuarios.permissions import usuario_tem_acesso_total_pastoral

        if user.is_superuser or usuario_tem_acesso_total_pastoral(user):
            return True

        roles = allowed_roles or DepartamentoMembro.PAPEIS_GESTAO_ESCALA
        return self.participacoes.filter(
            membro=user,
            ativo=True,
            papel__in=roles,
        ).exists()

    def save(self, *args, **kwargs):
        if self._state.adding or not self.codigo:
            self.codigo = self.gerar_codigo_unico()
        return super().save(*args, **kwargs)


class DepartamentoMembro(models.Model):
    class Papel(models.TextChoices):
        LIDER = "lider", "Lider"
        VICE_LIDER = "vice_lider", "Vice-lider"
        LIDERADO = "liderado", "Liderado"
        AUXILIAR = "auxiliar", "Auxiliar"
        VOLUNTARIO = "voluntario", "Voluntario"
        MEMBRO = "membro", "Membro (legado)"

    PAPEIS_LIDERANCA = (Papel.LIDER,)
    PAPEIS_GESTAO_ESCALA = PAPEIS_LIDERANCA
    PAPEIS_SERVICO = (
        Papel.LIDER,
        Papel.VICE_LIDER,
        Papel.LIDERADO,
        Papel.AUXILIAR,
        Papel.VOLUNTARIO,
        Papel.MEMBRO,
    )

    membro = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name="Membro",
        on_delete=models.PROTECT,
        related_name="participacoes_departamentais",
    )
    departamento = models.ForeignKey(
        Departamento,
        verbose_name="Departamento",
        on_delete=models.CASCADE,
        related_name="participacoes",
    )
    papel = models.CharField(
        "Papel no departamento",
        max_length=20,
        choices=Papel.choices,
        default=Papel.LIDERADO,
    )
    ativo = models.BooleanField("Ativo", default=True)
    data_entrada = models.DateField("Data de entrada", blank=True, null=True)
    observacoes = models.TextField("Observacoes", blank=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["departamento__nome", "membro__first_name", "membro__username"]
        verbose_name = "Membro do departamento"
        verbose_name_plural = "Membros do departamento"
        constraints = [
            models.UniqueConstraint(
                fields=["membro", "departamento"],
                condition=Q(ativo=True),
                name="uniq_participacao_ativa_por_departamento",
            )
        ]

    def __str__(self):
        return f"{self.membro} - {self.departamento} ({self.get_papel_display()})"


class DepartmentRole(models.Model):
    department = models.ForeignKey(
        Departamento,
        verbose_name="Departamento",
        on_delete=models.CASCADE,
        related_name="roles",
    )
    name = models.CharField("Nome", max_length=120)
    code = models.SlugField("Codigo", max_length=60)
    active = models.BooleanField("Ativo", default=True)
    can_manage_department = models.BooleanField("Pode gerenciar departamento", default=False)
    can_manage_members = models.BooleanField("Pode gerenciar pessoas", default=False)
    can_manage_schedules = models.BooleanField("Pode gerenciar escalas", default=False)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["department__nome", "name", "id"]
        verbose_name = "Cargo de departamento"
        verbose_name_plural = "Cargos de departamento"
        constraints = [
            models.UniqueConstraint(
                fields=["department", "code"],
                name="uniq_department_role_code_per_department",
            )
        ]
        permissions = [
            ("deactivate_departmentrole", "Can deactivate department role"),
            ("reactivate_departmentrole", "Can reactivate department role"),
        ]

    def __str__(self):
        return f"{self.department} - {self.name}"

    def save(self, *args, **kwargs):
        self.name = (self.name or "").strip()
        self.code = Departamento.normalizar_codigo(self.code or self.name)
        return super().save(*args, **kwargs)


class DepartmentMembership(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Ativa"
        INACTIVE = "INACTIVE", "Inativa"

    person = models.ForeignKey(
        "pessoas.Person",
        verbose_name="Pessoa",
        on_delete=models.PROTECT,
        related_name="department_memberships",
    )
    department = models.ForeignKey(
        Departamento,
        verbose_name="Departamento",
        on_delete=models.PROTECT,
        related_name="department_memberships",
    )
    role = models.ForeignKey(
        DepartmentRole,
        verbose_name="Cargo",
        on_delete=models.PROTECT,
        related_name="memberships",
    )
    status = models.CharField(
        "Status",
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )
    joined_at = models.DateField("Data de entrada", default=timezone.localdate)
    left_at = models.DateField("Data de saida", blank=True, null=True)
    created_at = models.DateTimeField("Criado em", auto_now_add=True)
    updated_at = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["department__nome", "person__full_name", "id"]
        verbose_name = "Pessoa no departamento"
        verbose_name_plural = "Pessoas nos departamentos"
        constraints = [
            models.UniqueConstraint(
                fields=["person", "department"],
                name="uniq_department_membership_person_department",
            )
        ]
        permissions = [
            ("deactivate_departmentmembership", "Can deactivate department membership"),
            ("reactivate_departmentmembership", "Can reactivate department membership"),
        ]

    def __str__(self):
        return f"{self.person} - {self.department} ({self.role})"


# Compatibilidade de import para o restante do projeto enquanto o dominio de escalas
# termina de migrar para o app dedicado.
from escalas.models import CultoPadrao, Escala, EscalaItem, IndisponibilidadeMembro  # noqa: E402


__all__ = [
    "CultoPadrao",
    "Departamento",
    "DepartamentoMembro",
    "DepartmentMembership",
    "DepartmentRole",
    "Escala",
    "EscalaItem",
    "IndisponibilidadeMembro",
]

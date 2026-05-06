import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import FileExtensionValidator
from django.db import models
from django.urls import reverse


MAX_IMAGE_SIZE = 5 * 1024 * 1024
IMAGE_EXTENSIONS = ["jpg", "jpeg", "png", "webp"]


def validate_image_size(file_obj):
    if file_obj and getattr(file_obj, "size", 0) > MAX_IMAGE_SIZE:
        raise ValidationError("A imagem deve ter no maximo 5 MB.")


image_validators = [
    FileExtensionValidator(allowed_extensions=IMAGE_EXTENSIONS),
    validate_image_size,
]


class Ministro(models.Model):
    class Tipo(models.TextChoices):
        CASA = "casa", "Ministro da casa"
        VISITANTE = "visitante", "Ministro visitante"

    class Status(models.TextChoices):
        PENDENTE = "pendente", "Pendente"
        APROVADO = "aprovado", "Aprovado"
        RECUSADO = "recusado", "Recusado"
        ATUALIZADO = "atualizado", "Atualizado"

    class TipoChavePix(models.TextChoices):
        CPF = "cpf", "CPF"
        CNPJ = "cnpj", "CNPJ"
        EMAIL = "email", "E-mail"
        TELEFONE = "telefone", "Telefone"
        ALEATORIA = "aleatoria", "Chave aleatoria"

    nome_completo = models.CharField("Nome completo", max_length=160)
    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        verbose_name="Usuario vinculado",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="perfil_ministerial",
    )
    nome_ministerial = models.CharField("Nome ministerial/publico", max_length=160, blank=True)
    tipo = models.CharField("Tipo", max_length=20, choices=Tipo.choices, default=Tipo.VISITANTE)
    status = models.CharField(
        "Status do cadastro",
        max_length=20,
        choices=Status.choices,
        default=Status.PENDENTE,
    )

    telefone_whatsapp = models.CharField("Telefone/WhatsApp", max_length=30, blank=True)
    email = models.EmailField("E-mail", blank=True)
    igreja_origem = models.CharField("Igreja/ministerio de origem", max_length=160, blank=True)
    cidade = models.CharField("Cidade", max_length=120, blank=True)
    estado = models.CharField("Estado", max_length=80, blank=True)
    pais = models.CharField("Pais", max_length=80, blank=True, default="Brasil")
    biografia = models.TextField("Biografia/resumo", blank=True)
    observacoes_internas = models.TextField("Observacoes internas", blank=True)
    foto_principal = models.ImageField(
        "Foto principal",
        upload_to="ministros/fotos/",
        blank=True,
        null=True,
        validators=image_validators,
    )

    tipo_chave_pix = models.CharField(
        "Tipo de chave PIX",
        max_length=20,
        choices=TipoChavePix.choices,
        blank=True,
    )
    chave_pix = models.CharField("Chave PIX", max_length=180, blank=True)
    qr_code_pix = models.ImageField(
        "QR Code PIX",
        upload_to="ministros/pix/",
        blank=True,
        null=True,
        validators=image_validators,
    )
    favorecido_nome = models.CharField("Nome do favorecido", max_length=160, blank=True)
    favorecido_documento = models.CharField("CPF/CNPJ do favorecido", max_length=30, blank=True)
    banco = models.CharField("Banco", max_length=120, blank=True)
    observacoes_financeiras = models.TextField("Observacoes financeiras", blank=True)

    restricao_alimentar = models.TextField("Restricao alimentar", blank=True)
    alergias = models.TextField("Alergias", blank=True)
    preferencia_alimentacao = models.TextField("Preferencia de alimentacao", blank=True)
    observacoes_hospedagem = models.TextField("Observacoes de hospedagem", blank=True)
    observacoes_transporte = models.TextField("Observacoes de transporte", blank=True)
    necessidades_especiais = models.TextField("Necessidades especiais", blank=True)

    token_formulario = models.UUIDField(
        "Token do formulario externo",
        default=uuid.uuid4,
        unique=True,
        editable=False,
    )
    ativo = models.BooleanField("Ativo", default=True)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["nome_ministerial", "nome_completo"]
        verbose_name = "Ministro"
        verbose_name_plural = "Ministros"

    def __str__(self):
        return self.nome_ministerial or self.nome_completo

    @property
    def nome_exibicao(self):
        return self.nome_ministerial or self.nome_completo

    @property
    def cidade_estado(self):
        partes = [parte for parte in [self.cidade, self.estado] if parte]
        return "/".join(partes)

    @property
    def foto_destaque(self):
        return self.fotos.filter(destaque=True).order_by("-criado_em").first()

    def get_formulario_externo_url(self):
        return reverse("ministros:formulario_externo", args=[self.token_formulario])

    def regenerar_token(self):
        self.token_formulario = uuid.uuid4()
        self.save(update_fields=["token_formulario", "atualizado_em"])


class FotoMinistro(models.Model):
    ministro = models.ForeignKey(
        Ministro,
        verbose_name="Ministro",
        on_delete=models.CASCADE,
        related_name="fotos",
    )
    imagem = models.ImageField(
        "Imagem",
        upload_to="ministros/galeria/",
        validators=image_validators,
    )
    legenda = models.CharField("Legenda", max_length=180, blank=True)
    destaque = models.BooleanField("Destaque", default=False)
    criado_em = models.DateTimeField("Criado em", auto_now_add=True)

    class Meta:
        ordering = ["-destaque", "-criado_em"]
        verbose_name = "Foto do ministro"
        verbose_name_plural = "Fotos dos ministros"

    def __str__(self):
        return f"{self.ministro} - {self.legenda or 'Foto'}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.destaque:
            FotoMinistro.objects.filter(ministro=self.ministro, destaque=True).exclude(pk=self.pk).update(
                destaque=False
            )

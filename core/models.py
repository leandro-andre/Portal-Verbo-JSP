import re
from urllib.parse import parse_qs, quote_plus, urlparse

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models


YOUTUBE_VIDEO_ID_REGEX = re.compile(r"^[A-Za-z0-9_-]{11}$")


def extract_youtube_video_id(url: str) -> str:
    url = (url or "").strip()
    if not url:
        return ""

    parsed = urlparse(url)
    host = (parsed.netloc or "").lower().replace("www.", "")
    path = (parsed.path or "").strip("/")

    if host in {"youtube.com", "m.youtube.com"}:
        if path == "watch":
            video_id = parse_qs(parsed.query).get("v", [""])[0].strip()
        elif path.startswith("embed/"):
            video_id = path.split("/", 1)[1].strip()
        else:
            return ""
    elif host == "youtu.be":
        video_id = path.split("/", 1)[0].strip()
    elif host == "youtube-nocookie.com" and path.startswith("embed/"):
        video_id = path.split("/", 1)[1].strip()
    else:
        return ""

    if not YOUTUBE_VIDEO_ID_REGEX.match(video_id):
        return ""
    return video_id


class SiteConfig(models.Model):
    """
    Configuracoes globais do site editaveis via painel/admin.
    Mantemos uma linha (singleton na pratica).
    """

    nome_igreja = models.CharField(max_length=120, default="Verbo da Vida - Jardim São Paulo")
    Logo_img = models.ImageField("Logo", upload_to="logo/", blank=True, null=True)

    telefone = models.CharField("Telefone fixo", max_length=20, blank=True)
    whatsapp = models.CharField(
        "WhatsApp",
        max_length=20,
        blank=True,
        help_text="Ex: (81) 90000-0000",
    )
    email = models.EmailField("E-mail corporativo", blank=True)
    endereco = models.CharField(
        "Endereço completo",
        max_length=255,
        blank=True,
        help_text="Ex: R. Dr. Gustavo Pinto, 72 - Estância, Recife - PE, 50781-740",
    )

    instagram = models.URLField("Instagram", blank=True, help_text="Link completo do perfil")
    facebook = models.URLField("Facebook", blank=True, help_text="Link completo da página")

    texto_institucional = models.TextField(
        "Texto institucional curto",
        blank=True,
        help_text="Usado no rodapé ou banners pequenos. Exemplo: 'Um lugar para crescer em fé...'",
    )
    horarios_cultos = models.TextField(
        "Horários principais",
        blank=True,
        help_text="Exibidos na home e footer. Coloque um por linha. Ex: 'Domingo — 19:00'",
    )

    youtube_embed_url = models.URLField(
        "Link Ao Vivo (YouTube)",
        blank=True,
        help_text="Cole uma URL do YouTube nos formatos embed, watch ou youtu.be.",
    )
    hero_home = models.ImageField(
        "Hero da Home",
        upload_to="site/heroes/",
        blank=True,
        null=True,
        help_text="Imagem de fundo usada no topo da pagina inicial.",
    )
    hero_sobre = models.ImageField(
        "Hero do Sobre",
        upload_to="site/heroes/",
        blank=True,
        null=True,
        help_text="Imagem de fundo usada no topo da pagina Sobre.",
    )
    hero_agenda = models.ImageField(
        "Hero da Agenda",
        upload_to="site/heroes/",
        blank=True,
        null=True,
        help_text="Imagem de fundo usada no topo da pagina Agenda.",
    )
    hero_noticias = models.ImageField(
        "Hero das Noticias",
        upload_to="site/heroes/",
        blank=True,
        null=True,
        help_text="Imagem de fundo usada no topo da pagina de noticias.",
    )
    hero_ao_vivo = models.ImageField(
        "Hero do Ao Vivo",
        upload_to="site/heroes/",
        blank=True,
        null=True,
        help_text="Imagem de fundo usada no topo da pagina Ao Vivo.",
    )
    hero_contato = models.ImageField(
        "Hero do Contato",
        upload_to="site/heroes/",
        blank=True,
        null=True,
        help_text="Imagem de fundo usada no topo da pagina Contato.",
    )
    mapa_embed_url = models.URLField(
        "Link de incorporação do Google Maps",
        max_length=2000,
        blank=True,
        help_text="Cole a URL usada no iframe de incorporação do Google Maps.",
    )
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuração do site"
        verbose_name_plural = "Configuração do site"

    def __str__(self) -> str:
        return f"Configurações - {self.nome_igreja}"

    def clean(self):
        super().clean()
        if self.youtube_embed_url:
            self.youtube_embed_url = self.youtube_embed_url.strip()
            video_id = extract_youtube_video_id(self.youtube_embed_url)
            if not video_id:
                raise ValidationError(
                    {
                        "youtube_embed_url": "Informe uma URL válida do YouTube com um vídeo válido."
                    }
                )
            self.youtube_embed_url = f"https://www.youtube-nocookie.com/embed/{video_id}"

        if self.mapa_embed_url:
            self.mapa_embed_url = self.mapa_embed_url.strip()

    @property
    def youtube_video_id(self) -> str:
        return extract_youtube_video_id(self.youtube_embed_url)

    @property
    def youtube_embed_url_normalized(self) -> str:
        if self.youtube_video_id:
            return f"https://www.youtube-nocookie.com/embed/{self.youtube_video_id}"
        return ""

    @property
    def youtube_watch_url(self) -> str:
        if self.youtube_video_id:
            return f"https://www.youtube.com/watch?v={self.youtube_video_id}"
        return (self.youtube_embed_url or "").strip()

    @property
    def maps_search_url(self) -> str:
        endereco = (self.endereco or "").strip()
        if not endereco:
            return ""
        return f"https://www.google.com/maps/search/?api=1&query={quote_plus(endereco)}"

    @property
    def maps_embed_url_resolved(self) -> str:
        return (self.mapa_embed_url or "").strip()

    def horarios_cultos_lista(self) -> list[str]:
        return [h.strip() for h in self.horarios_cultos.split("\n") if h.strip()]


class SobrePage(models.Model):
    """
    Conteudo editorial da pagina Sobre.
    Singleton na pratica (id=1).
    """

    banner_titulo = models.CharField(
        "Título do banner",
        max_length=120,
        default="Sobre nós",
    )
    banner_subtitulo = models.CharField(
        "Subtítulo do banner",
        max_length=255,
        default="Conheça nossa história, nossa missão e o propósito que nos move.",
    )

    historia_titulo = models.CharField(
        "Título da seção história",
        max_length=120,
        default="Nossa história",
    )
    historia_texto = models.TextField(
        "Texto da história",
        default=(
            "Nossa igreja nasceu do desejo de ver pessoas se aproximando de Deus "
            "e vivendo uma fé prática: que transforma o coração, fortalece famílias "
            "e gera propósito para o dia a dia.\n\n"
            "Somos uma comunidade acolhedora, com espaço para todas as idades, "
            "caminhando juntos em comunhão, serviço e crescimento espiritual."
        ),
        help_text="Separe parágrafos com linhas em branco.",
    )

    missao = models.TextField(
        "Missão",
        default="Anunciar o evangelho e formar discípulos, conectando pessoas a Deus e à comunidade, com amor e clareza.",
    )
    visao = models.TextField(
        "Visão",
        default="Ser uma igreja relevante e acolhedora, que inspira fé, comunhão e serviço, impactando nossa cidade.",
    )
    valores = models.TextField(
        "Valores",
        default="Bíblia como fundamento, comunhão, excelência com simplicidade, generosidade e cuidado com pessoas.",
    )

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Página Sobre"
        verbose_name_plural = "Página Sobre"

    def __str__(self) -> str:
        return "Página Sobre"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls) -> "SobrePage":
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj

    def historia_paragrafos(self) -> list[str]:
        return [p.strip() for p in self.historia_texto.split("\n\n") if p.strip()]


class Lider(models.Model):
    """
    Líderes exibidos na seção de liderança da página Sobre.
    """

    sobre_page = models.ForeignKey(
        SobrePage,
        on_delete=models.CASCADE,
        related_name="lideres",
        verbose_name="Página Sobre",
        default=1,
    )
    nome = models.CharField("Nome", max_length=120)
    cargo = models.CharField("Cargo / função", max_length=120)
    descricao = models.TextField("Descrição", blank=True)
    foto = models.ImageField(
        "Foto",
        upload_to="lideres/",
        blank=True,
        null=True,
        help_text="Tamanho recomendado: 400×400 px.",
    )
    ordem = models.PositiveIntegerField(
        "Ordem de exibição",
        default=0,
        help_text="Menor número aparece primeiro.",
    )

    class Meta:
        verbose_name = "Líder"
        verbose_name_plural = "Líderes"
        ordering = ["ordem", "nome"]

    def __str__(self) -> str:
        return f"{self.nome} — {self.cargo}"


class ContatoMensagem(models.Model):
    """Mensagem enviada pelo formulario de contato do portal."""

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="mensagens_contato",
        blank=True,
        null=True,
    )
    nome = models.CharField("Nome", max_length=120)
    email = models.EmailField("E-mail")
    assunto = models.CharField("Assunto", max_length=160, blank=True)
    mensagem = models.TextField("Mensagem")
    respondida = models.BooleanField("Respondida", default=False)
    criado_em = models.DateTimeField("Recebida em", auto_now_add=True)
    atualizado_em = models.DateTimeField("Atualizada em", auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Mensagem de contato"
        verbose_name_plural = "Mensagens de contato"

    def __str__(self) -> str:
        assunto = self.assunto or "Sem assunto"
        return f"{self.nome} - {assunto}"

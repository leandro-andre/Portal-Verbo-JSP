from django.db import models
from django.utils import timezone
from django.utils.text import slugify


class Noticia(models.Model):
    titulo = models.CharField("Título", max_length=200)
    slug = models.SlugField(
        "Slug",
        max_length=200,
        unique=True,
        blank=True,
        help_text="URL amigável da notícia. Caso deixe em branco, será gerado automaticamente.",
    )
    resumo = models.TextField(
        "Resumo",
        blank=True,
        help_text="Texto curto exibido nos cards (na listagem e na home).",
    )
    conteudo = models.TextField("Conteúdo", help_text="Suporta HTML/Markdown se integrado no frontend.")
    imagem = models.ImageField(
        "Imagem",
        upload_to="noticias/",
        blank=True,
        null=True,
    )
    
    publicado = models.BooleanField("Publicado", default=True)
    destaque_home = models.BooleanField(
        "Destaque na Home",
        default=False,
        help_text="Marque para aparecer na seção Últimas Notícias da homepage.",
    )
    
    data_publicacao = models.DateField("Data da publicação", default=timezone.now)
    criado_em = models.DateTimeField("Criado em", default=timezone.now)
    atualizado_em = models.DateTimeField("Atualizado em", auto_now=True)

    class Meta:
        ordering = ["-data_publicacao", "-criado_em"]
        verbose_name = "Notícia"
        verbose_name_plural = "Notícias"

    def __str__(self) -> str:
        return self.titulo

    def gerar_slug_unico(self) -> str:
        base_slug = slugify(self.titulo) or "noticia"
        slug = base_slug
        contador = 2

        while Noticia.objects.filter(slug=slug).exclude(pk=self.pk).exists():
            slug = f"{base_slug}-{contador}"
            contador += 1

        return slug

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = self.gerar_slug_unico()
        super().save(*args, **kwargs)

from django.contrib import admin
from django.utils.html import format_html

from governanca.admin_mixins import GovernedContentAdminMixin

from .models import Noticia


@admin.register(Noticia)
class NoticiaAdmin(GovernedContentAdminMixin, admin.ModelAdmin):
    """Gerenciamento de notícias."""

    list_display = (
        "titulo",
        "data_publicacao",
        "publicado",
        "destaque_home",
        "miniatura",
    )
    list_display_links = ("titulo",)
    list_filter = ("publicado", "destaque_home", "data_publicacao")
    list_editable = ("publicado", "destaque_home")
    search_fields = ("titulo", "resumo", "conteudo")
    prepopulated_fields = {"slug": ("titulo",)}
    date_hierarchy = "data_publicacao"

    fieldsets = (
        (None, {
            "fields": ("titulo", "slug", "resumo", "conteudo"),
        }),
        ("Mídia", {
            "fields": ("imagem", "preview_imagem"),
        }),
        ("Publicação e Destaque", {
            "fields": ("publicado", "destaque_home", "data_publicacao"),
            "description": "Notícias destacadas aparecerão na página inicial.",
        }),
    )

    readonly_fields = ("preview_imagem",)

    @admin.display(description="Imagem")
    def miniatura(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:6px;object-fit:cover;" />',
                obj.imagem.url,
            )
        return "—"

    @admin.display(description="Preview")
    def preview_imagem(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="max-height:200px;border-radius:12px;object-fit:cover;" />',
                obj.imagem.url,
            )
        return "Sem imagem."

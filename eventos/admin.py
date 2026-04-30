from django.contrib import admin
from django.utils.html import format_html

from governanca.admin_mixins import GovernedContentAdminMixin

from .models import Evento


@admin.register(Evento)
class EventoAdmin(GovernedContentAdminMixin, admin.ModelAdmin):
    """Gerenciamento de eventos com interface profissional."""

    list_display = (
        "titulo",
        "data",
        "horario",
        "tipo_display",
        "publicado",
        "destaque_home",
        "miniatura",
    )
    list_display_links = ("titulo",)
    list_filter = ("publicado", "destaque_home", "tipo", "data")
    list_editable = ("publicado", "destaque_home")
    search_fields = ("titulo", "descricao", "local")
    ordering = ("-data", "-horario")
    date_hierarchy = "data"

    fieldsets = (
        (None, {
            "fields": ("titulo", "descricao"),
        }),
        ("Data e local", {
            "fields": ("data", "horario", "local"),
        }),
        ("Classificação", {
            "fields": ("tipo",),
        }),
        ("Imagem", {
            "fields": ("imagem", "preview_imagem"),
        }),
        ("Publicação", {
            "fields": ("publicado", "destaque_home"),
            "description": "Marque 'destaque home' para exibir este evento na página inicial.",
        }),
    )

    readonly_fields = ("preview_imagem",)

    @admin.display(description="Tipo")
    def tipo_display(self, obj):
        return obj.get_tipo_display() or "—"

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
        return "Nenhuma imagem enviada."

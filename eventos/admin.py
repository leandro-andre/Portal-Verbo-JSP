from django.contrib import admin
from django.utils.html import format_html

from governanca.admin_mixins import GovernedContentAdminMixin

from .models import Evento, InscricaoEvento


@admin.register(Evento)
class EventoAdmin(GovernedContentAdminMixin, admin.ModelAdmin):
    list_display = (
        "titulo",
        "data_inicio",
        "horario",
        "tipo_display",
        "publicado",
        "inscricoes_abertas",
        "capacidade_maxima",
        "destaque_home",
        "miniatura",
    )
    list_display_links = ("titulo",)
    list_filter = ("publicado", "inscricoes_abertas", "destaque_home", "tipo", "data_inicio")
    list_editable = ("publicado", "inscricoes_abertas", "destaque_home")
    search_fields = ("titulo", "descricao", "local")
    ordering = ("-data_inicio", "-horario")
    date_hierarchy = "data_inicio"

    fieldsets = (
        (None, {
            "fields": ("titulo", "descricao"),
        }),
        ("Data e local", {
            "fields": ("data_inicio", "data_fim", "horario", "local"),
        }),
        ("Classificacao", {
            "fields": ("tipo",),
        }),
        ("Inscricoes", {
            "fields": ("capacidade_maxima", "inscricoes_abertas"),
        }),
        ("Imagem", {
            "fields": ("imagem", "preview_imagem"),
        }),
        ("Publicacao", {
            "fields": ("publicado", "destaque_home"),
        }),
    )

    readonly_fields = ("preview_imagem",)

    @admin.display(description="Tipo")
    def tipo_display(self, obj):
        return obj.get_tipo_display() or "-"

    @admin.display(description="Imagem")
    def miniatura(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="height:36px;border-radius:6px;object-fit:cover;" />',
                obj.imagem.url,
            )
        return "-"

    @admin.display(description="Preview")
    def preview_imagem(self, obj):
        if obj.imagem:
            return format_html(
                '<img src="{}" style="max-height:200px;border-radius:12px;object-fit:cover;" />',
                obj.imagem.url,
            )
        return "Nenhuma imagem enviada."


@admin.register(InscricaoEvento)
class InscricaoEventoAdmin(admin.ModelAdmin):
    list_display = ("nome", "evento", "email", "telefone", "status", "presente_em")
    list_filter = ("status", "evento")
    search_fields = ("nome", "email", "telefone", "evento__titulo")
    autocomplete_fields = ("evento", "usuario", "checkin_por")
    readonly_fields = ("criado_em", "atualizado_em", "presente_em", "checkin_por")

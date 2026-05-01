from django.contrib import admin

from .models import FotoMinistro, Ministro


class FotoMinistroInline(admin.TabularInline):
    model = FotoMinistro
    extra = 1


@admin.register(Ministro)
class MinistroAdmin(admin.ModelAdmin):
    list_display = ("nome_exibicao", "tipo", "cidade", "estado", "status", "ativo")
    list_filter = ("tipo", "status", "ativo")
    search_fields = ("nome_completo", "nome_ministerial", "igreja_origem", "cidade")
    readonly_fields = ("token_formulario", "criado_em", "atualizado_em")
    inlines = [FotoMinistroInline]


@admin.register(FotoMinistro)
class FotoMinistroAdmin(admin.ModelAdmin):
    list_display = ("ministro", "legenda", "destaque", "criado_em")
    list_filter = ("destaque",)
    search_fields = ("ministro__nome_completo", "ministro__nome_ministerial", "legenda")
